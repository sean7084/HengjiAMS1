from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from companies.models import Company
from reports.models import ReportSchedule, ReportTemplate


class ReportScheduleTimeHandlingTests(TestCase):
    """Regression coverage for issue #68.

    ``should_run()`` and ``record_success()`` called ``datetime.now()`` while
    ``reports/models.py`` never imported ``datetime`` at module level, so both
    raised ``NameError`` on every invocation. The same methods also used naive
    datetimes even though ``USE_TZ = True``, which cannot be compared with the
    aware values Django stores. Everything now goes through
    ``django.utils.timezone``.
    """

    def setUp(self):
        self.company = Company.objects.create(name='Kering', code='KER')
        self.template = ReportTemplate.objects.create(
            name='Asset Inventory',
            code='asset-inventory',
            report_type='asset_inventory',
        )

    def _make_schedule(self, **overrides):
        fields = {
            'name': 'Daily inventory',
            'template': self.template,
            'frequency': ReportSchedule.Frequency.DAILY,
            'start_date': timezone.localdate(),
            'company': self.company,
            'status': ReportSchedule.ScheduleStatus.ACTIVE,
            'is_active': True,
        }
        fields.update(overrides)
        return ReportSchedule.objects.create(**fields)

    def test_should_run_false_when_inactive(self):
        schedule = self._make_schedule(
            is_active=False, next_run=timezone.now() - timezone.timedelta(hours=1)
        )
        self.assertIs(schedule.should_run(), False)

    def test_should_run_false_when_end_date_has_passed(self):
        # This path evaluated `datetime.now().date()` -> NameError before the fix.
        schedule = self._make_schedule(
            end_date=timezone.localdate() - timezone.timedelta(days=1),
            next_run=timezone.now() - timezone.timedelta(hours=1),
        )
        self.assertIs(schedule.should_run(), False)

    def test_should_run_true_when_due(self):
        # This path compared `datetime.now() >= self.next_run` -> NameError, and
        # would have compared a naive against an aware datetime even if imported.
        schedule = self._make_schedule(next_run=timezone.now() - timezone.timedelta(minutes=5))
        self.assertIs(schedule.should_run(), True)

    def test_should_run_false_when_not_yet_due(self):
        schedule = self._make_schedule(next_run=timezone.now() + timezone.timedelta(hours=1))
        self.assertIs(schedule.should_run(), False)

    def test_should_run_false_without_next_run(self):
        schedule = self._make_schedule(next_run=None)
        self.assertIs(schedule.should_run(), False)

    def test_record_success_persists_aware_last_run(self):
        # This path assigned `datetime.now()` -> NameError before the fix.
        schedule = self._make_schedule(next_run=timezone.now() - timezone.timedelta(minutes=5))
        schedule.record_success()
        schedule.refresh_from_db()
        self.assertIsNotNone(schedule.last_run)
        self.assertTrue(timezone.is_aware(schedule.last_run))
        self.assertEqual(schedule.consecutive_failures, 0)
        self.assertEqual(schedule.last_error, '')

    def test_record_success_advances_next_run(self):
        schedule = self._make_schedule(next_run=timezone.now() - timezone.timedelta(minutes=5))
        before = timezone.now()
        schedule.record_success()
        schedule.refresh_from_db()
        self.assertIsNotNone(schedule.next_run)
        self.assertTrue(timezone.is_aware(schedule.next_run))
        self.assertGreater(schedule.next_run, before)

    def test_calculate_next_run_without_last_run_is_aware(self):
        schedule = self._make_schedule(last_run=None, next_run=None)
        schedule.calculate_next_run()
        schedule.refresh_from_db()
        self.assertIsNotNone(schedule.next_run)
        self.assertTrue(timezone.is_aware(schedule.next_run))

    def test_record_failure_pauses_after_max_failures(self):
        schedule = self._make_schedule(max_failures=2)
        schedule.record_failure('boom')
        self.assertEqual(schedule.consecutive_failures, 1)
        self.assertEqual(schedule.status, ReportSchedule.ScheduleStatus.ACTIVE)
        schedule.record_failure('boom again')
        schedule.refresh_from_db()
        self.assertEqual(schedule.consecutive_failures, 2)
        self.assertEqual(schedule.status, ReportSchedule.ScheduleStatus.PAUSED)
        self.assertIs(schedule.should_run(), False)
