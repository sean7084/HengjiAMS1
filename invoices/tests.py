from django.test import TestCase
import datetime

from .models import InvoiceInfo, WeeklyOrderBatch


class InvoiceNumberGenerationTests(TestCase):
    def test_invoice_number_increments_for_same_day(self):
        batch = WeeklyOrderBatch.objects.create(sharepoint_file='invoices/sharepoint/dummy.xlsx')

        first = InvoiceInfo.objects.create(
            weekly_batch=batch,
            invoice_date=datetime.date(2026, 4, 16),
            kering_group_po_number='PO-001',
            internal_order='IO-001',
            sap_cost_center='CC-001',
            source_row_number=2,
        )
        second = InvoiceInfo.objects.create(
            weekly_batch=batch,
            invoice_date=datetime.date(2026, 4, 16),
            kering_group_po_number='PO-002',
            internal_order='IO-002',
            sap_cost_center='CC-002',
            source_row_number=3,
        )

        self.assertEqual(first.invoice_number, '26041601')
        self.assertEqual(second.invoice_number, '26041602')
