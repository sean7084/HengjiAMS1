from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from companies.models import Company

from .forms import QuotationForm
from .models import DEFAULT_QUOTATION_REMARK_POLICY_LINE, Quotation
from .services import split_quotation_items_for_pdf


class QuotationRemarkTests(TestCase):
    def test_form_exposes_prefilled_remarks_before_notes(self):
        form = QuotationForm()

        self.assertLess(list(form.fields).index('remarks'), list(form.fields).index('notes'))

        self.assertEqual(form['remarks'].value(), form.initial['remarks'])
        self.assertIn('1. 此报价为', form.initial['remarks'])
        self.assertIn(DEFAULT_QUOTATION_REMARK_POLICY_LINE, form.initial['remarks'])
        self.assertNotIn('placeholder', form.fields['remarks'].widget.attrs)

    def test_build_default_remarks_uses_unique_item_targets(self):
        quotation = Quotation(customer=Company(name='BV', code='BV'))
        ordered_items = [
            SimpleNamespace(user_brand='BV', user_name='Cindy Sheng'),
            SimpleNamespace(user_brand='BV', user_name='Cindy Sheng'),
            SimpleNamespace(user_brand='', user_name='Leo'),
        ]

        self.assertEqual(
            quotation.build_default_remarks(ordered_items=ordered_items),
            '1. 此报价为 BV Cindy Sheng, Leo 采购项目。\n2. 全部产品保修遵循相关官方政策。',
        )

    def test_get_effective_remarks_prefers_custom_text(self):
        quotation = Quotation(
            customer=Company(name='BV', code='BV'),
            remarks='1. Custom project remark.\n2. Custom warranty note.',
        )

        self.assertEqual(
            quotation.get_effective_remarks(ordered_items=[]),
            '1. Custom project remark.\n2. Custom warranty note.',
        )


class QuotationPdfSplitTests(TestCase):
    def test_split_quotation_items_for_pdf_separates_hardware_and_services(self):
        ordered_items = [
            SimpleNamespace(
                service_item_id=None,
                brand_name='Lenovo',
                product_description='ThinkPad',
                user_brand='BV',
                user_name='Alice',
                unit='PCS',
                unit_price=Decimal('100.00'),
                tax_rate=Decimal('13.00'),
                quantity=2,
                line_total_without_tax=Decimal('200.00'),
                line_total_with_tax=Decimal('226.00'),
                tax_amount=Decimal('26.00'),
            ),
            SimpleNamespace(
                service_item_id=1,
                brand_name='Onsite',
                product_description='Support',
                user_brand='BV',
                user_name='Alice',
                unit='JOB',
                unit_price=Decimal('50.00'),
                tax_rate=Decimal('6.00'),
                quantity=1,
                line_total_without_tax=Decimal('50.00'),
                line_total_with_tax=Decimal('53.00'),
                tax_amount=Decimal('3.00'),
            ),
        ]

        result = split_quotation_items_for_pdf(ordered_items)

        self.assertEqual(len(result['hardware_items']), 1)
        self.assertEqual(len(result['service_items']), 1)
        self.assertEqual(result['hardware_totals']['total_without_tax'], Decimal('200.00'))
        self.assertEqual(result['hardware_totals']['total_tax'], Decimal('26.00'))
        self.assertEqual(result['hardware_totals']['total_with_tax'], Decimal('226.00'))
        self.assertEqual(result['service_totals']['total_without_tax'], Decimal('50.00'))
        self.assertEqual(result['service_totals']['total_tax'], Decimal('3.00'))
        self.assertEqual(result['service_totals']['total_with_tax'], Decimal('53.00'))