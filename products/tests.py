from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import AdminRole, User
from assets.models import AssetBrand, AssetCategory, AssetModel

from .models import ProductPrice, ProductPriceApprovalRequest


class ProductPriceApprovalWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.manager_role = AdminRole.objects.get(code=User.AdminRole.ORDER_MANAGEMENT_MANAGER)
        cls.specialist_role = AdminRole.objects.get(code=User.AdminRole.ORDER_MANAGEMENT_SPECIALIST)

        cls.manager_user = User.objects.create_user(username='manager_user', password='TestPass123!')
        cls.manager_user.roles.add(cls.manager_role)

        cls.specialist_user = User.objects.create_user(username='specialist_user', password='TestPass123!')
        cls.specialist_user.roles.add(cls.specialist_role)

        cls.category = AssetCategory.objects.create(name='Laptops', code='LAPTOPS')
        cls.brand = AssetBrand.objects.create(name='Dell', code='DELL')
        cls.model = AssetModel.objects.create(
            brand=cls.brand,
            category=cls.category,
            name='XPS 13',
            model_number='XPS-13',
        )

    def _create_live_price(self, *, price_without_tax=Decimal('100.00')):
        return ProductPrice.objects.create(
            brand=self.brand,
            model=self.model,
            unit='PCS',
            price_without_tax=price_without_tax,
            tax_rate=Decimal('13.00'),
            is_current=True,
            valid_from=timezone.localdate(),
        )

    def _build_price_payload(self, *, price_without_tax='100.00', notes='Pending review'):
        return {
            'model': str(self.model.pk),
            'unit': 'PCS',
            'price_without_tax': price_without_tax,
            'tax_rate': '13.00',
            'price_with_tax': str((Decimal(price_without_tax) * Decimal('1.13')).quantize(Decimal('0.01'))),
            'is_current': 'on',
            'valid_from': timezone.localdate().isoformat(),
            'valid_until': '',
            'notes': notes,
        }

    def test_specialist_create_submits_pending_request(self):
        self.client.force_login(self.specialist_user)

        response = self.client.post(
            reverse('products:price_add'),
            self._build_price_payload(price_without_tax='100.00'),
        )

        self.assertRedirects(response, reverse('products:price_list'))
        self.assertFalse(ProductPrice.objects.filter(model=self.model, is_current=True).exists())

        approval_request = ProductPriceApprovalRequest.objects.get()
        self.assertEqual(approval_request.request_type, ProductPriceApprovalRequest.RequestType.CREATE)
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.PENDING)
        self.assertEqual(approval_request.requested_by, self.specialist_user)
        self.assertEqual(approval_request.target_model, self.model)

    def test_manager_approval_applies_specialist_create_request(self):
        self.client.force_login(self.specialist_user)
        self.client.post(
            reverse('products:price_add'),
            self._build_price_payload(price_without_tax='100.00'),
        )
        approval_request = ProductPriceApprovalRequest.objects.get()

        self.client.force_login(self.manager_user)
        response = self.client.post(
            reverse('products:approval_request_detail', args=[approval_request.pk]),
            {
                'action': 'approve',
                'review_notes': 'Approved for rollout.',
            },
        )

        self.assertRedirects(response, reverse('products:approval_request_detail', args=[approval_request.pk]))

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.APPROVED)
        self.assertEqual(approval_request.reviewed_by, self.manager_user)
        self.assertTrue(ProductPrice.objects.filter(model=self.model, is_current=True).exists())

    def test_manager_can_open_approval_list_and_detail_pages(self):
        self.client.force_login(self.specialist_user)
        self.client.post(
            reverse('products:price_add'),
            self._build_price_payload(price_without_tax='100.00'),
        )
        approval_request = ProductPriceApprovalRequest.objects.get()

        self.client.force_login(self.manager_user)
        list_response = self.client.get(reverse('products:approval_request_list'))
        detail_response = self.client.get(reverse('products:approval_request_detail', args=[approval_request.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Price Approval Requests')
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, approval_request.catalog_label)

    def test_specialist_update_stays_pending_until_manager_approval(self):
        price = self._create_live_price(price_without_tax=Decimal('100.00'))

        self.client.force_login(self.specialist_user)
        response = self.client.post(
            reverse('products:price_edit', args=[price.pk]),
            self._build_price_payload(price_without_tax='120.00', notes='Increase requested'),
        )

        self.assertRedirects(response, reverse('products:price_list'))
        price.refresh_from_db()
        self.assertEqual(price.price_without_tax, Decimal('100.00'))

        approval_request = ProductPriceApprovalRequest.objects.get(
            request_type=ProductPriceApprovalRequest.RequestType.UPDATE,
            target_price=price,
        )
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.PENDING)

        self.client.force_login(self.manager_user)
        self.client.post(
            reverse('products:approval_request_detail', args=[approval_request.pk]),
            {'action': 'approve'},
        )

        price.refresh_from_db()
        approval_request.refresh_from_db()
        self.assertEqual(price.price_without_tax, Decimal('120.00'))
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.APPROVED)

    def test_specialist_price_list_shows_pending_request_badge_on_row(self):
        price = self._create_live_price(price_without_tax=Decimal('100.00'))

        self.client.force_login(self.specialist_user)
        self.client.post(
            reverse('products:price_edit', args=[price.pk]),
            self._build_price_payload(price_without_tax='120.00', notes='Increase requested'),
        )
        approval_request = ProductPriceApprovalRequest.objects.get(
            request_type=ProductPriceApprovalRequest.RequestType.UPDATE,
            target_price=price,
        )

        response = self.client.get(reverse('products:price_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Update Request Pending')
        self.assertContains(response, reverse('products:approval_request_detail', args=[approval_request.pk]))

    def test_specialist_delete_stays_live_until_manager_approval(self):
        price = self._create_live_price(price_without_tax=Decimal('100.00'))

        self.client.force_login(self.specialist_user)
        response = self.client.post(reverse('products:price_delete', args=[price.pk]))

        self.assertRedirects(response, reverse('products:price_list'))
        self.assertTrue(ProductPrice.objects.filter(pk=price.pk).exists())

        approval_request = ProductPriceApprovalRequest.objects.get(
            request_type=ProductPriceApprovalRequest.RequestType.DELETE,
        )
        self.assertEqual(approval_request.target_price, price)
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.PENDING)

        self.client.force_login(self.manager_user)
        self.client.post(
            reverse('products:approval_request_detail', args=[approval_request.pk]),
            {'action': 'approve'},
        )

        approval_request.refresh_from_db()
        self.assertEqual(approval_request.status, ProductPriceApprovalRequest.Status.APPROVED)
        self.assertFalse(ProductPrice.objects.filter(pk=price.pk).exists())

    def test_specialist_cannot_access_import_page(self):
        self.client.force_login(self.specialist_user)

        response = self.client.get(reverse('products:price_import'))

        self.assertRedirects(response, reverse('products:price_list'))