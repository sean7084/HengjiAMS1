"""Tests for iteration-2 features: AM/PM slot move, review page, bundle export,
WiFi weak points, FE assignment, and the not-found mandatory-note validation.
"""
import io
import json
import zipfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APIClient

from accounts.models import AdminRole
from companies.models import Company, Division, Location
from inspections.forms import WifiWeakPointFormSet
from inspections.models import (
    InspectionBatch, InspectionDevice, InspectionWifiWeakPoint, StoreInspection,
)

User = get_user_model()


def _ensure_roles():
    for code, name in [('superadmin', 'Superadmin'), ('inspection_engineer', 'Field Engineer')]:
        AdminRole.objects.get_or_create(code=code, defaults={'name': name, 'is_active': True})


def _png_bytes(color='steelblue'):
    buffer = io.BytesIO()
    Image.new('RGB', (8, 8), color).save(buffer, format='PNG')
    return buffer.getvalue()


class Iteration2FixtureMixin:
    def setUp(self):
        _ensure_roles()
        # DRF client for the mini-program API endpoints (JSON payloads); the
        # Django client stays on self.client for the server-rendered web views.
        self.api = APIClient()
        self.company = Company.objects.create(name='Kering', code='KER')
        self.division = Division.objects.create(company=self.company, name='Gucci', code='GUCCI')
        self.location = Location.objects.create(
            company=self.company, division=self.division, name='SZOL', code='22149',
            location_type=Location.LocationType.STORE,
        )
        self.superadmin = User.objects.create_user(username='admin', password='pw')
        self.superadmin.set_admin_roles([User.AdminRole.SUPERADMIN])
        self.engineer = User.objects.create_user(username='fe', password='pw')
        self.engineer.set_admin_roles([User.AdminRole.INSPECTION_ENGINEER])
        self.inspection = StoreInspection.objects.create(
            company=self.company, division=self.division, location=self.location,
            jda_code='22149', brand_name='Gucci', store_name='SZOL',
            store_label='22149 Gucci SZOL', inspection_date=date(2026, 10, 5),
            slot=StoreInspection.Slot.AM, engineer=self.engineer,
        )

    def make_device(self, **kwargs):
        defaults = {'client_device_uid': f'd{InspectionDevice.objects.count()}',
                    'category': 'Desktop', 'brand_model': 'Lenovo-M70Q', 'sn': 'SN1'}
        defaults.update(kwargs)
        return InspectionDevice.objects.create(store_inspection=self.inspection, **defaults)


class SlotMoveTests(Iteration2FixtureMixin, TestCase):
    def test_manager_can_move_to_pm(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:inspection_move'),
            data=json.dumps({'inspection_id': str(self.inspection.id),
                             'date': '2026-10-06', 'slot': 'pm'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.inspection_date, date(2026, 10, 6))
        self.assertEqual(self.inspection.slot, StoreInspection.Slot.PM)

    def test_invalid_slot_rejected(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:inspection_move'),
            data=json.dumps({'inspection_id': str(self.inspection.id),
                             'date': '2026-10-06', 'slot': 'night'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)

    def test_engineer_cannot_move(self):
        self.client.force_login(self.engineer)
        response = self.client.post(
            reverse('inspections:inspection_move'),
            data=json.dumps({'inspection_id': str(self.inspection.id),
                             'date': '2026-10-06', 'slot': 'pm'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)


class DashboardGridTests(Iteration2FixtureMixin, TestCase):
    def test_days_json_groups_by_slot(self):
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse('inspections:dashboard'), {'month': '2026-10'})
        self.assertEqual(response.status_code, 200)
        days = json.loads(response.context['days_json'])
        target = next(d for d in days if d['date'] == '2026-10-05')
        self.assertEqual(len(target['am']), 1)
        self.assertEqual(target['am'][0]['label'], '22149 Gucci SZOL')
        self.assertEqual(target['pm'], [])


class ReviewPageTests(Iteration2FixtureMixin, TestCase):
    def test_review_counts(self):
        self.make_device()                      # expected, not collected
        self.make_device(client_device_uid='new1', is_new_device=True)
        self.client.force_login(self.superadmin)
        response = self.client.get(reverse('inspections:review'), {'period': 'custom',
                                                                   'date_from': '2026-10-01',
                                                                   'date_to': '2026-10-31'})
        self.assertEqual(response.status_code, 200)
        rows = response.context['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['expected'], 1)
        self.assertEqual(rows[0]['new_found'], 1)
        self.assertEqual(rows[0]['collected'], 0)

    def test_bulk_update_status(self):
        device = self.make_device()
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:review_bulk'),
            {'device_ids': [str(device.id)], 'status': 'not_in_store'},
        )
        self.assertEqual(response.status_code, 302)
        device.refresh_from_db()
        self.assertEqual(device.status, 'not_in_store')

    def test_bulk_update_by_site_only_touches_outstanding_devices(self):
        outstanding = self.make_device()
        collected = self.make_device(client_device_uid='c1', collected_at=timezone.now())
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:review_bulk'),
            {'inspection_ids': [str(self.inspection.id)], 'status': 'not_in_store'},
        )
        self.assertEqual(response.status_code, 302)
        outstanding.refresh_from_db()
        collected.refresh_from_db()
        self.assertEqual(outstanding.status, 'not_in_store')
        # The mandatory-note invariant holds: a not-found device carries a reason.
        self.assertTrue(outstanding.comment)
        self.assertNotEqual(collected.status, 'not_in_store')

    def test_engineer_cannot_bulk_update(self):
        device = self.make_device()
        self.client.force_login(self.engineer)
        response = self.client.post(
            reverse('inspections:review_bulk'),
            {'device_ids': [str(device.id)], 'status': 'not_in_store'},
        )
        self.assertEqual(response.status_code, 403)


class WifiWeakPointTests(Iteration2FixtureMixin, TestCase):
    def test_post_weak_points_sets_coverage_weak(self):
        self.api.force_authenticate(self.engineer)
        response = self.api.post(
            f"/api/v1/inspections/{self.inspection.id}/wifi-weak-points/",
            {'weak_points': [{'location': 'back office', 'description': 'dead zone'}]},
            format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.wifi_coverage, StoreInspection.WifiCoverage.WEAK)
        self.assertEqual(self.inspection.wifi_weak_points.count(), 1)

    def test_empty_weak_points_sets_coverage_good(self):
        InspectionWifiWeakPoint.objects.create(
            store_inspection=self.inspection, location='x', description='y')
        self.api.force_authenticate(self.engineer)
        response = self.api.post(
            f"/api/v1/inspections/{self.inspection.id}/wifi-weak-points/",
            {'weak_points': []}, format='json',
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.wifi_coverage, StoreInspection.WifiCoverage.GOOD)
        self.assertEqual(self.inspection.wifi_weak_points.count(), 0)


class DeviceNoteValidationTests(Iteration2FixtureMixin, TestCase):
    def test_not_in_store_requires_comment(self):
        self.api.force_authenticate(self.engineer)
        response = self.api.post(
            f"/api/v1/inspections/{self.inspection.id}/devices/",
            {'client_device_uid': 'nf1', 'status': 'not_in_store', 'comment': ''},
            format='json',
        )
        self.assertEqual(response.status_code, 400, response.content)

    def test_not_in_store_with_comment_ok(self):
        self.api.force_authenticate(self.engineer)
        response = self.api.post(
            f"/api/v1/inspections/{self.inspection.id}/devices/",
            {'client_device_uid': 'nf2', 'status': 'not_in_store', 'comment': 'missing from store'},
            format='json',
        )
        self.assertIn(response.status_code, (200, 201), response.content)


class AssignFeTests(Iteration2FixtureMixin, TestCase):
    def test_assign_creates_fe_when_missing(self):
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:assign_fe', args=[self.inspection.id]),
            {'query': 'Zhang San', 'create_if_missing': '1'},
        )
        self.assertEqual(response.status_code, 302)
        self.inspection.refresh_from_db()
        self.assertEqual(self.inspection.engineer.chinese_name, 'Zhang San')
        self.assertTrue(self.inspection.engineer.is_field_engineer())
        self.assertTrue(self.inspection.engineer.invite_code)


class ProfileCompletionTests(Iteration2FixtureMixin, TestCase):
    """Invite-code field engineers complete their contact details on first login."""

    def _make_invite_engineer(self, username):
        fe = User.objects.create_user(username=username, password='pw')
        fe.set_admin_roles([User.AdminRole.INSPECTION_ENGINEER])
        fe.chinese_name = ''
        fe.phone_number = ''
        fe.save()
        return fe

    def test_invite_code_is_generated_for_field_engineer(self):
        fe = self._make_invite_engineer('fe_invite')
        self.assertTrue(fe.invite_code)
        self.assertTrue(fe.is_field_engineer())

    def test_profile_completion_fills_blank_fields(self):
        fe = self._make_invite_engineer('fe_invite2')
        self.api.force_authenticate(fe)
        response = self.api.post('/api/v1/auth/wechat/profile/', {
            'chinese_name': '张三', 'phone_number': '13800000000', 'wechat_id': 'zs_wx',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        fe.refresh_from_db()
        self.assertEqual(fe.chinese_name, '张三')
        self.assertEqual(fe.phone_number, '13800000000')
        self.assertEqual(fe.wechat_id, 'zs_wx')
        self.assertEqual(
            sorted(response.data['updated']),
            ['chinese_name', 'phone_number', 'wechat_id'],
        )

    def test_profile_completion_never_overwrites_admin_values(self):
        fe = User.objects.create_user(username='fe_complete', password='pw')
        fe.chinese_name = '李四'
        fe.phone_number = '13900000000'
        fe.save()
        self.api.force_authenticate(fe)
        response = self.api.post('/api/v1/auth/wechat/profile/', {
            'chinese_name': '王五', 'phone_number': '13700000000',
        }, format='json')
        self.assertEqual(response.status_code, 200, response.content)
        fe.refresh_from_db()
        self.assertEqual(fe.chinese_name, '李四')
        self.assertEqual(fe.phone_number, '13900000000')
        self.assertEqual(response.data['updated'], [])

    def test_profile_completion_requires_auth(self):
        response = self.api.post('/api/v1/auth/wechat/profile/', {'chinese_name': 'x'}, format='json')
        self.assertIn(response.status_code, (401, 403))


class BackendEditPageTests(Iteration2FixtureMixin, TestCase):
    """Manual backend override of onsite-captured data (times, WiFi, weak points)."""

    def test_detail_page_lists_wifi_weak_points(self):
        InspectionWifiWeakPoint.objects.create(
            store_inspection=self.inspection, location='后仓', description='信号弱，扫码超时。')
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse('inspections:inspection_detail', args=[self.inspection.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WiFi Weak Points')
        self.assertContains(response, '后仓')

    def test_edit_page_renders_existing_weak_point(self):
        InspectionWifiWeakPoint.objects.create(
            store_inspection=self.inspection, location='后仓', description='信号弱。')
        self.client.force_login(self.superadmin)
        response = self.client.get(
            reverse('inspections:inspection_edit', args=[self.inspection.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'WiFi Weak Points')
        self.assertContains(response, '后仓')

    def test_edit_page_saves_times_and_weak_points(self):
        prefix = WifiWeakPointFormSet.get_default_prefix()
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:inspection_edit', args=[self.inspection.id]),
            {
                'engineer': self.engineer.id,
                'arriving_time': '09:15',
                'leaving_time': '11:45',
                'wifi_coverage': StoreInspection.WifiCoverage.GOOD,
                'it_support_rating': StoreInspection.ItSupportRating.SATISFIED,
                'it_support_comment': '响应及时',
                'notes': 'backend edit',
                f'{prefix}-TOTAL_FORMS': '1',
                f'{prefix}-INITIAL_FORMS': '0',
                f'{prefix}-MIN_NUM_FORMS': '0',
                f'{prefix}-MAX_NUM_FORMS': '1000',
                f'{prefix}-0-id': '',
                f'{prefix}-0-sort_index': '0',
                f'{prefix}-0-location': 'back office',
                f'{prefix}-0-description': 'dead zone',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.inspection.refresh_from_db()
        self.assertEqual(str(self.inspection.arriving_time), '09:15:00')
        self.assertEqual(str(self.inspection.leaving_time), '11:45:00')
        self.assertEqual(self.inspection.wifi_weak_points.count(), 1)
        # Coverage is re-derived from the weak points, not taken from the form.
        self.assertEqual(self.inspection.wifi_coverage, StoreInspection.WifiCoverage.WEAK)

    def test_engineer_cannot_open_edit_page(self):
        self.client.force_login(self.engineer)
        response = self.client.get(
            reverse('inspections:inspection_edit', args=[self.inspection.id]))
        self.assertEqual(response.status_code, 403)


class BundleExportTests(Iteration2FixtureMixin, TestCase):
    def test_bundle_zip_contains_asset_list(self):
        self.make_device()
        self.client.force_login(self.superadmin)
        response = self.client.post(
            reverse('inspections:asset_list_export'),
            {'batch': '', 'division': self.division.id, 'include_asset_list': 'on',
             'include_photos': 'on'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('zip', response['Content-Type'])
        # Stream the response content into a zip and check the asset list entry.
        content = b''.join(response.streaming_content) if response.streaming else response.content
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            self.assertIn('asset_list.xlsx', zf.namelist())

    def test_bundle_folders_are_unique_when_a_store_has_two_slots(self):
        """AM and PM visits of one store must not collide inside the ZIP."""
        from inspections.models import InspectionPhoto
        from inspections.services.bundle_export import build_bundle

        pm = StoreInspection.objects.create(
            company=self.company, division=self.division, location=self.location,
            jda_code='22149', brand_name='Gucci', store_name='SZOL',
            store_label='22149 Gucci SZOL', inspection_date=date(2026, 10, 5),
            slot=StoreInspection.Slot.PM,
        )
        for inspection in (self.inspection, pm):
            photo = InspectionPhoto(store_inspection=inspection, kind='overall', sort_index=1)
            photo.image.save('overall.png', ContentFile(_png_bytes()), save=False)
            photo.save()

        tmp = build_bundle([self.inspection, pm], include_photos=True, include_reports=False)
        with zipfile.ZipFile(tmp) as zf:
            names = zf.namelist()
        self.assertEqual(len(names), len(set(names)), f'duplicate zip entries: {names}')
        self.assertTrue(any('2026-10-05 AM' in name for name in names), names)
        self.assertTrue(any('2026-10-05 PM' in name for name in names), names)
