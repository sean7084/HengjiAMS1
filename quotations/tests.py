from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase

from companies.models import Company

from .forms import QuotationForm
from .models import DEFAULT_QUOTATION_REMARK_POLICY_LINE, Quotation
from .services import render_quotation_pdf_html, split_quotation_items_for_pdf


class QuotationRemarkTests(TestCase):
    def test_form_exposes_prefilled_remarks_before_notes(self):
        form = QuotationForm()

        self.assertLess(list(form.fields).index('remarks'), list(form.fields).index('notes'))

        self.assertEqual(form['remarks'].value(), form.initial['remarks'])
        self.assertIn('1. 此报价为', form.initial['remarks'])
        self.assertIn(DEFAULT_QUOTATION_REMARK_POLICY_LINE, form.initial['remarks'])
        self.assertNotIn('placeholder', form.fields['remarks'].widget.attrs)

    def test_form_defaults_pdf_template_from_customer(self):
        company = Company.objects.create(
            name='BV',
            code='BV',
            default_quotation_template='v1',
        )

        form = QuotationForm(initial={'customer': company.pk})

        self.assertEqual(form.initial['pdf_template'], 'v1')

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
                model_number='20XW',
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
                model_number='SVC-01',
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

    @patch('quotations.services.HTML')
    @patch('quotations.services.render_to_string')
    def test_render_quotation_pdf_html_uses_selected_template(self, render_to_string_mock, html_class_mock):
        company = Company.objects.create(name='BV', code='BV')
        quotation = Quotation.objects.create(
            customer=company,
            valid_until='2026-01-01',
            pdf_template='v1',
        )

        html_instance = html_class_mock.return_value
        html_instance.write_pdf.return_value = b'pdf-bytes'
        render_to_string_mock.return_value = '<html></html>'

        result = render_quotation_pdf_html(quotation)

        self.assertEqual(result, b'pdf-bytes')
        render_to_string_mock.assert_called_once()
        self.assertEqual(render_to_string_mock.call_args.args[0], 'quotations/template_v1.html')

    def test_render_quotation_pdf_html_renders_all_registered_templates(self):
        company = Company.objects.create(name='Rendered BV', code='RBV')
        quotation = Quotation.objects.create(
            customer=company,
            valid_until='2026-01-01',
        )

        for template_code in ['v1', 'v2_full', 'v2_mini']:
            with self.subTest(template_code=template_code):
                pdf_bytes = render_quotation_pdf_html(quotation, template_code=template_code)
                self.assertTrue(pdf_bytes.startswith(b'%PDF'))

    @patch('quotations.services.HTML')
    def test_render_quotation_pdf_html_renders_customer_name_in_confirmed_by_section(self, html_class_mock):
        company = Company.objects.create(name='Confirmed Target Co', code='CTC')
        quotation = Quotation.objects.create(
            customer=company,
            valid_until='2026-01-01',
        )

        html_class_mock.return_value.write_pdf.return_value = b'pdf-bytes'

        for template_code in ['v1', 'v2_full']:
            with self.subTest(template_code=template_code):
                render_quotation_pdf_html(quotation, template_code=template_code)
                html_output = html_class_mock.call_args.kwargs['string']
                self.assertIn('Confirmed By :', html_output)
                self.assertIn(f'class="sign-value">{company.name}</td>', html_output)
                self.assertIn('sample_contact_seal.png', html_output)