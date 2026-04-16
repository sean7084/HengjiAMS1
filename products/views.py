"""
Views for Products app.
"""
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import HttpResponse, HttpResponseRedirect
from django.core.paginator import Paginator
from django.db import models

from assets.models import AssetBrand
from .models import ProductPrice
from .forms import ProductPriceForm


class ProductPriceListView(ListView):
    """List view for product prices with filtering."""
    model = ProductPrice
    template_name = 'products/price_list.html'
    context_object_name = 'prices'
    paginate_by = 20

    def get_queryset(self):
        queryset = ProductPrice.objects.all().select_related('brand', 'model')

        # Filter by brand
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        # Search by brand name or model name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(brand__name__icontains=search) |
                models.Q(model__name__icontains=search) |
                models.Q(model__model_number__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = AssetBrand.objects.filter(is_active=True).order_by('name')
        context['selected_brand'] = self.request.GET.get('brand', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ProductPriceCreateView(CreateView):
    """Create view for product prices."""
    model = ProductPrice
    form_class = ProductPriceForm
    template_name = 'products/price_form.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price created successfully.')
        return super().form_valid(form)


class ProductPriceUpdateView(UpdateView):
    """Update view for product prices."""
    model = ProductPrice
    form_class = ProductPriceForm
    template_name = 'products/price_form.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price updated successfully.')
        return super().form_valid(form)


class ProductPriceDeleteView(DeleteView):
    """Delete view for product prices."""
    model = ProductPrice
    template_name = 'products/price_confirm_delete.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price deleted successfully.')
        return super().form_valid(form)


def import_prices_view(request):
    """Import product prices from Excel file."""
    from django.conf import settings
    import openpyxl
    from io import BytesIO
    import datetime

    if request.method == 'POST' and request.FILES.get('file'):
        excel_file = request.FILES['file']
        workbook = openpyxl.load_workbook(excel_file)
        sheet = workbook.active

        # Get headers from first row
        headers = [cell.value for cell in sheet[1]]
        expected_headers = ['Brand_Code', 'Model_Number', 'Unit', 'Price_Without_Tax', 'Tax_Rate']

        # Validate headers
        if headers[:len(expected_headers)] != expected_headers:
            messages.error(request, f'Invalid file format. Expected headers: {", ".join(expected_headers)}')
            return redirect('products:price_import')

        success_count = 0
        error_count = 0
        errors = []

        for row_num, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row[0]:  # Skip empty rows
                continue

            try:
                brand_code = str(row[0]).strip()
                model_number = str(row[1]).strip() if row[1] else ''
                unit = str(row[2]).strip() if row[2] else 'PCS'
                price_without_tax = float(row[3]) if row[3] else 0
                tax_rate = float(row[4]) if row[4] else 13.00

                # Find brand and model
                brand = AssetBrand.objects.filter(code=brand_code).first()
                if not brand:
                    errors.append(f"Row {row_num}: Brand code '{brand_code}' not found")
                    error_count += 1
                    continue

                model = brand.models.filter(model_number=model_number).first()
                if not model:
                    errors.append(f"Row {row_num}: Model number '{model_number}' not found for brand '{brand_code}'")
                    error_count += 1
                    continue

                # Create or update price
                price_with_tax = price_without_tax * (1 + tax_rate / 100)
                price, created = ProductPrice.objects.update_or_create(
                    brand=brand,
                    model=model,
                    defaults={
                        'unit': unit,
                        'price_without_tax': price_without_tax,
                        'price_with_tax': price_with_tax,
                        'tax_rate': tax_rate,
                        'is_current': True,
                    }
                )
                success_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                error_count += 1

        messages.success(request, f'Import completed: {success_count} prices imported, {error_count} errors.')
        if errors:
            for error in errors[:10]:  # Show first 10 errors
                messages.warning(request, error)

        return redirect('products:price_list')

    return render(request, 'products/import_prices.html')


def download_import_template(request):
    """Download Excel template for price import."""
    import openpyxl
    from io import BytesIO

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Product Prices"

    # Add headers
    headers = ['Brand_Code', 'Model_Number', 'Unit', 'Price_Without_Tax', 'Tax_Rate']
    sheet.append(headers)

    # Add example row
    sheet.append(['DELL', 'XPS-15', 'PCS', '9999.00', '13.00'])

    # Auto-adjust column widths
    for column in sheet.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        sheet.column_dimensions[column_letter].width = adjusted_width

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=product_price_import_template.xlsx'
    workbook.save(response)
    return response
