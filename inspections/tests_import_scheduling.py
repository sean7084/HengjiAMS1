"""Tests for schedule auto-arrangement (R1) and importer Location population.

Covers ``inspections/services/schedule_arranger.py`` (city clustering, same-address
consecutive AM/PM slots, capacity overflow) and the ``kering_import`` integration
that fills ``companies.Location`` contact/geography fields and assigns slots when
the schedule has no ``inspection_date``.
"""
import io
from datetime import date

import pandas as pd
from django.contrib.auth import get_user_model
from django.test import TestCase

from companies.models import Company, Location
from inspections.models import StoreInspection
from inspections.services import kering_import
from inspections.services.schedule_arranger import ScheduleCapacityError, arrange

User = get_user_model()


def _xlsx_bytes(rows):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pd.DataFrame(rows).to_excel(writer, index=False, sheet_name='Sheet1')
    buffer.seek(0)
    return buffer


class ScheduleArrangerTests(TestCase):
    def test_same_address_gets_consecutive_slots(self):
        rows = [
            {'city': 'Beijing', 'address': 'Beijing SKP', 'store': 'BJSK'},
            {'city': 'Beijing', 'address': 'Beijing SKP', 'store': 'BJSC'},
            {'city': 'Beijing', 'address': 'Beijing SKP', 'store': 'BJKD'},
        ]
        out = arrange(rows, date(2026, 10, 1), date(2026, 10, 3))
        # Three co-located sites occupy consecutive slots: AM d1, PM d1, AM d2.
        self.assertEqual(
            [(r['inspection_date'], r['slot']) for r in out],
            [(date(2026, 10, 1), 'am'), (date(2026, 10, 1), 'pm'), (date(2026, 10, 2), 'am')],
        )

    def test_cities_are_spread_across_range(self):
        rows = [
            {'city': 'Beijing', 'address': 'A1', 'store': 'S1'},
            {'city': 'Beijing', 'address': 'A1', 'store': 'S2'},
            {'city': 'Shanghai', 'address': 'B1', 'store': 'S3'},
            {'city': 'Shanghai', 'address': 'B1', 'store': 'S4'},
        ]
        out = arrange(rows, date(2026, 10, 1), date(2026, 10, 2))
        by_store = {r['store']: (r['inspection_date'], r['slot']) for r in out}
        # Beijing takes the first contiguous block, Shanghai the second.
        self.assertEqual(by_store['S1'], (date(2026, 10, 1), 'am'))
        self.assertEqual(by_store['S2'], (date(2026, 10, 1), 'pm'))
        self.assertEqual(by_store['S3'], (date(2026, 10, 2), 'am'))
        self.assertEqual(by_store['S4'], (date(2026, 10, 2), 'pm'))

    def test_capacity_overflow_raises(self):
        rows = [{'city': 'C', 'address': f'A{i}', 'store': f'S{i}'} for i in range(5)]
        with self.assertRaises(ScheduleCapacityError):
            arrange(rows, date(2026, 10, 1), date(2026, 10, 2))  # only 4 slots

    def test_empty_rows_returns_empty(self):
        self.assertEqual(arrange([], date(2026, 10, 1), date(2026, 10, 2)), [])


class ImporterLocationAndAutoArrangeTests(TestCase):
    def setUp(self):
        self.company = Company.objects.create(name='Kering', code='KER')

    def _schedule_without_dates(self):
        return _xlsx_bytes([
            {'Brand': 'Gucci', 'Store Name': 'BJSK', 'JDA code': 22032,
             'Address': 'No.87 Jian Guo Road, Beijing SKP', 'City': 'Beijing',
             'Store Dir. Phone': '+8610 65981606', 'device_count': 71},
            {'Brand': 'Gucci', 'Store Name': 'BJSC', 'JDA code': 22152,
             'Address': 'No.87 Jian Guo Road, Beijing SKP', 'City': 'Beijing',
             'Store Dir. Phone': '+8610 65000957', 'device_count': 18},
            {'Brand': 'Gucci', 'Store Name': 'SZOL', 'JDA code': 22149,
             'Address': 'Shanghai Qiantan Ave 1', 'City': 'Shanghai',
             'Store Dir. Phone': '+8621 11112222', 'device_count': 30},
        ])

    def test_location_fields_populated_and_auto_arrange_assigns_slots(self):
        kering_import.import_kering_master(
            self._schedule_without_dates(),
            None,
            company_name='Kering',
            company_code='KER',
            batch=None,
            auto_arrange=True,
            arrange_start=date(2026, 11, 2),
            arrange_end=date(2026, 11, 4),
        )
        # Locations carry address/city/phone from the schedule.
        skp = Location.objects.get(code='22032')
        self.assertEqual(skp.city, 'Beijing')
        self.assertEqual(skp.address_line1, 'No.87 Jian Guo Road, Beijing SKP')
        self.assertEqual(skp.phone_number, '+8610 65981606')

        # Same-address Beijing sites are consecutive (AM/PM same date); Shanghai after.
        inspections = {i.jda_code: i for i in StoreInspection.objects.all()}
        self.assertEqual(inspections['22032'].inspection_date, date(2026, 11, 2))
        self.assertEqual(inspections['22032'].slot, 'am')
        self.assertEqual(inspections['22152'].inspection_date, date(2026, 11, 2))
        self.assertEqual(inspections['22152'].slot, 'pm')
        self.assertEqual(inspections['22149'].inspection_date, date(2026, 11, 3))
        self.assertEqual(inspections['22149'].slot, 'am')

    def test_missing_dates_without_auto_arrange_are_skipped(self):
        kering_import.import_kering_master(
            self._schedule_without_dates(),
            None,
            company_name='Kering',
            company_code='KER',
            batch=None,
            auto_arrange=False,
        )
        # No inspections created (rows lacked dates), but locations still imported.
        self.assertEqual(StoreInspection.objects.count(), 0)
        self.assertEqual(Location.objects.count(), 3)
