"""
Views for Products app.
"""
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from django.db import models

from assets.models import AssetBrand, AssetModel
from assets.models import AssetCategory
from .models import ProductPrice, ServiceItem
from .forms import ProductPriceForm, ServicePriceForm


class OrderManagementAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.can_manage_orders()

    def handle_no_permission(self):
        messages.error(self.request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')


class ProductModelCatalogMixin:
    """Provide model metadata for derived form fields and search UI."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        models_qs = AssetModel.objects.filter(is_active=True).exclude(
            category__item_type=AssetCategory.ItemType.SERVICE,
        ).select_related('brand').order_by('brand__name', 'name')
        context['model_catalog'] = [
            {
                'id': str(asset_model.pk),
                'brand_name': asset_model.brand.name,
                'unit': asset_model.unit or 'PCS',
                'label': str(asset_model),
                'model_number': asset_model.model_number or '',
            }
            for asset_model in models_qs
        ]
        return context


class ProductPriceListView(OrderManagementAccessMixin, ListView):
    """List view for product prices with filtering."""
    model = ProductPrice
    template_name = 'products/price_list.html'
    context_object_name = 'prices'
    paginate_by = 20

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('category_id')
        default_model_id = request.POST.get('default_model_id')
        category = AssetCategory.objects.filter(pk=category_id, is_active=True).first()
        if not category:
            messages.error(request, 'Selected category was not found.')
            return redirect('products:price_list')

        if default_model_id:
            model = AssetModel.objects.filter(pk=default_model_id, is_active=True, category=category).first()
            if not model:
                messages.error(request, 'Selected default model does not belong to this category.')
                return redirect('products:price_list')
            category.default_asset_model = model
            category.save(update_fields=['default_asset_model', 'updated_at'])
            messages.success(request, 'Default model updated successfully.')
        else:
            category.default_asset_model = None
            category.save(update_fields=['default_asset_model', 'updated_at'])
            messages.success(request, 'Default model cleared successfully.')
        return redirect('products:price_list')

    def get_queryset(self):
        queryset = ProductPrice.objects.all().select_related('brand', 'model', 'model__category', 'service_item')

        self.selected_type = self.request.GET.get('type') or 'all'
        if self.selected_type not in {'all', AssetCategory.ItemType.HARDWARE, AssetCategory.ItemType.SERVICE}:
            self.selected_type = 'all'

        self.selected_status = self.request.GET.get('status') or 'current'
        if self.selected_status not in {'current', 'inactive', 'all'}:
            self.selected_status = 'current'

        if self.selected_type == AssetCategory.ItemType.SERVICE:
            queryset = queryset.filter(service_item__isnull=False)
        elif self.selected_type == AssetCategory.ItemType.HARDWARE:
            queryset = queryset.filter(model__isnull=False)

        if self.selected_status == 'current':
            queryset = queryset.filter(is_current=True)
        elif self.selected_status == 'inactive':
            queryset = queryset.filter(is_current=False)

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
                models.Q(model__model_number__icontains=search) |
                models.Q(model__description__icontains=search) |
                models.Q(service_item__name__icontains=search) |
                models.Q(service_item__service_group__icontains=search) |
                models.Q(service_item__description__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = AssetBrand.objects.filter(is_active=True).order_by('name')
        context['selected_brand'] = self.request.GET.get('brand', '')
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_type'] = getattr(self, 'selected_type', 'all')
        context['selected_status'] = getattr(self, 'selected_status', 'current')
        categories = AssetCategory.objects.filter(
            is_active=True,
        ).exclude(
            item_type=AssetCategory.ItemType.SERVICE,
        ).prefetch_related('asset_models__brand').select_related('default_asset_model__brand').order_by('name')
        context['category_default_models'] = [
            {
                'category': category,
                'models': category.asset_models.filter(is_active=True).select_related('brand').order_by('brand__name', 'name'),
            }
            for category in categories
        ]
        return context


class ProductPriceCreateView(OrderManagementAccessMixin, ProductModelCatalogMixin, CreateView):
    """Create view for product prices."""
    model = ProductPrice
    form_class = ProductPriceForm
    template_name = 'products/price_form.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price created successfully.')
        return super().form_valid(form)


class ServicePriceCreateView(OrderManagementAccessMixin, FormView):
    """Create a service item and price in one step."""

    template_name = 'products/service_price_form.html'
    form_class = ServicePriceForm
    success_url = reverse_lazy('products:price_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_group_suggestions'] = list(
            ServiceItem.objects.exclude(service_group='').order_by('service_group').values_list('service_group', flat=True).distinct()
        )
        context['product_price'] = None
        return context

    def form_valid(self, form):
        try:
            form.save()
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Service item created successfully.')
        return super().form_valid(form)


class ServicePriceUpdateView(OrderManagementAccessMixin, FormView):
    """Edit a service item and its price entry."""

    template_name = 'products/service_price_form.html'
    form_class = ServicePriceForm
    success_url = reverse_lazy('products:price_list')

    def dispatch(self, request, *args, **kwargs):
        self.product_price = ProductPrice.objects.select_related('service_item').filter(
            pk=kwargs['pk'],
            service_item__isnull=False,
        ).first()
        if not self.product_price:
            messages.error(request, 'Service price was not found.')
            return redirect('products:price_list')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['product_price'] = self.product_price
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['service_group_suggestions'] = list(
            ServiceItem.objects.exclude(service_group='').order_by('service_group').values_list('service_group', flat=True).distinct()
        )
        context['product_price'] = self.product_price
        return context

    def form_valid(self, form):
        try:
            form.save(product_price=self.product_price, service_item=self.product_price.service_item)
        except ValidationError as exc:
            form.add_error(None, exc)
            return self.form_invalid(form)

        messages.success(self.request, 'Service item updated successfully.')
        return super().form_valid(form)


class ProductPriceUpdateView(OrderManagementAccessMixin, ProductModelCatalogMixin, UpdateView):
    """Update view for product prices."""
    model = ProductPrice
    form_class = ProductPriceForm
    template_name = 'products/price_form.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price updated successfully.')
        return super().form_valid(form)


class ProductPriceDeleteView(OrderManagementAccessMixin, DeleteView):
    """Delete view for product prices."""
    model = ProductPrice
    template_name = 'products/price_confirm_delete.html'
    success_url = reverse_lazy('products:price_list')

    def form_valid(self, form):
        messages.success(self.request, 'Product price deleted successfully.')
        return super().form_valid(form)


def import_prices_view(request):
    """Import product prices from Excel file."""
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')
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
                price, created = ProductPrice.objects.filter(is_current=True).update_or_create(
                    model=model,
                    defaults={
                        'brand': model.brand,
                        'unit': model.unit or 'PCS',
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
    if not request.user.can_manage_orders():
        messages.error(request, 'You do not have access to Order Management.')
        return redirect('dashboard:dashboard')
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
