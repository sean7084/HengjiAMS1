"""
Views for Assets app - Asset Management System.
Provides CRUD operations, search, filtering, and reporting for assets.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.db.models import Q, Count, Sum
from django.http import JsonResponse, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db import transaction
from django.conf import settings
import csv
import datetime
import pandas as pd
import io
from decimal import Decimal, InvalidOperation

from .models import Asset, AssetCategory, AssetBrand, AssetModel, AssetAssignment, AssetMaintenance
from .forms import AssetForm, AssetSearchForm, AssetAssignmentForm, AssetImportForm, AssetExportForm, BrandForm, CategoryForm, ModelForm
from companies.models import Company, Division, Location
from audit.models import AuditLog


class AssetListView(LoginRequiredMixin, ListView):
    """List view for assets with filtering and search capabilities."""
    model = Asset
    template_name = 'assets/asset_list.html'
    context_object_name = 'assets'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = self.request.user.get_accessible_assets().select_related(
            'category', 'brand', 'company', 'assigned_to'
        )
        
        # Apply filters
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(asset_number__icontains=search_query) |
                Q(name__icontains=search_query) |
                Q(serial_number__icontains=search_query)
            )
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        location = self.request.GET.get('location')
        if location:
            queryset = queryset.filter(current_location__icontains=location)
        
        # Ordering
        order_by = self.request.GET.get('order_by', '-created_at')
        queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = AssetCategory.objects.filter(is_active=True)
        context['locations'] = Location.objects.filter(status='active')
        context['search_form'] = AssetSearchForm(self.request.GET)
        context['status_choices'] = Asset.AssetStatus.choices
        
        # Stats for dashboard cards
        context['total_assets'] = self.get_queryset().count()
        context['available_assets'] = self.get_queryset().filter(status='available').count()
        context['assigned_assets'] = self.get_queryset().filter(status='assigned').count()
        context['maintenance_assets'] = self.get_queryset().filter(status='maintenance').count()
        
        return context


class AssetDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of a single asset."""
    model = Asset
    template_name = 'assets/asset_detail.html'
    context_object_name = 'asset'
    
    def get_object(self):
        accessible_assets = self.request.user.get_accessible_assets()
        obj = get_object_or_404(accessible_assets, pk=self.kwargs['pk'])
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        asset = self.get_object()
        
        # Get assignment history
        context['assignments'] = AssetAssignment.objects.filter(
            asset=asset
        ).select_related('assigned_to', 'assigned_by').order_by('-assigned_date')
        
        # Get maintenance history
        context['maintenance_records'] = AssetMaintenance.objects.filter(
            asset=asset
        ).order_by('-scheduled_date')
        
        # Get audit logs for this asset
        context['audit_logs'] = AuditLog.objects.filter(
            object_id=str(asset.pk),
            content_type__model='asset'
        ).select_related('user').order_by('-timestamp')[:10]
        
        return context


class AssetCreateView(LoginRequiredMixin, CreateView):
    """Create new asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    success_url = reverse_lazy('assets:asset_list')
    
    def form_valid(self, form):
        form.instance.company = self.request.user.company
        form.instance.created_by = self.request.user
        
        with transaction.atomic():
            response = super().form_valid(form)
            
            # Log the creation
            AuditLog.objects.create(
                user=self.request.user,
                company=self.request.user.company,
                action=AuditLog.ActionType.CREATE,
                content_object=self.object,
                description=f'Created asset: {self.object.asset_number}',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                self.request,
                _('Asset "{}" has been created successfully.').format(self.object.asset_number)
            )
            
            return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class AssetUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing asset."""
    model = Asset
    form_class = AssetForm
    template_name = 'assets/asset_form.html'
    
    def get_object(self):
        accessible_assets = self.request.user.get_accessible_assets()
        return get_object_or_404(accessible_assets, pk=self.kwargs['pk'])
    
    def form_valid(self, form):
        with transaction.atomic():
            # Store original values for audit log
            original_asset = Asset.objects.get(pk=self.object.pk)
            changes = []
            
            for field in form.changed_data:
                old_value = getattr(original_asset, field)
                new_value = form.cleaned_data[field]
                changes.append(f'{field}: {old_value} → {new_value}')
            
            response = super().form_valid(form)
            
            # Log the update
            if changes:
                AuditLog.objects.create(
                    user=self.request.user,
                    company=self.request.user.company,
                    action=AuditLog.ActionType.UPDATE,
                    content_object=self.object,
                    description=f'Updated asset: {self.object.asset_number}. Changes: {", ".join(changes)}',
                    ip_address=self.request.META.get('REMOTE_ADDR'),
                    user_agent=self.request.META.get('HTTP_USER_AGENT', '')
                )
            
            messages.success(
                self.request,
                _('Asset "{}" has been updated successfully.').format(self.object.asset_number)
            )
            
            return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_success_url(self):
        return reverse('assets:asset_detail', kwargs={'pk': self.object.pk})


class AssetDeleteView(LoginRequiredMixin, DeleteView):
    """Delete asset (soft delete)."""
    model = Asset
    template_name = 'assets/asset_delete.html'
    success_url = reverse_lazy('assets:asset_list')
    
    def get_object(self):
        accessible_assets = self.request.user.get_accessible_assets()
        return get_object_or_404(accessible_assets, pk=self.kwargs['pk'])
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        with transaction.atomic():
            # Soft delete - mark as retired instead of actual deletion
            self.object.status = 'retired'
            self.object.save()
            
            # Log the deletion
            AuditLog.objects.create(
                user=request.user,
                company=request.user.company,
                action=AuditLog.ActionType.DELETE,
                content_object=self.object,
                description=f'Deleted (retired) asset: {self.object.asset_number}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                request,
                _('Asset "{}" has been retired successfully.').format(self.object.asset_number)
            )
        
        return redirect(self.success_url)


@login_required
def asset_assign_view(request, pk):
    """Assign asset to a user."""
    accessible_assets = request.user.get_accessible_assets()
    asset = get_object_or_404(accessible_assets, pk=pk)
    
    if request.method == 'POST':
        form = AssetAssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            with transaction.atomic():
                # Return current assignment if exists
                current_assignment = AssetAssignment.objects.filter(
                    asset=asset, returned_date__isnull=True
                ).first()
                
                if current_assignment:
                    current_assignment.returned_date = datetime.datetime.now()
                    current_assignment.returned_by = request.user
                    current_assignment.save()
                
                # Create new assignment
                assignment = form.save(commit=False)
                assignment.asset = asset
                assignment.assigned_by = request.user
                assignment.save()
                
                # Update asset status
                asset.status = 'assigned'
                asset.assigned_to = assignment.assigned_to
                asset.save()
                
                # Log the assignment
                AuditLog.objects.create(
                    user=request.user,
                    company=request.user.company,
                    action=AuditLog.ActionType.ASSIGN,
                    content_object=asset,
                    description=f'Assigned asset {asset.asset_number} to {assignment.assigned_to.get_display_name()}',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(
                    request,
                    _('Asset "{}" has been assigned to {}.').format(
                        asset.asset_number, assignment.assigned_to.get_display_name()
                    )
                )
                
                return redirect('assets:asset_detail', pk=asset.pk)
    else:
        form = AssetAssignmentForm(user=request.user)
    
    return render(request, 'assets/asset_assign.html', {
        'asset': asset,
        'form': form
    })


@login_required
def asset_return_view(request, pk):
    """Return asset from current assignment."""
    accessible_assets = request.user.get_accessible_assets()
    asset = get_object_or_404(accessible_assets, pk=pk)
    
    current_assignment = AssetAssignment.objects.filter(
        asset=asset, returned_at__isnull=True
    ).first()
    
    if not current_assignment:
        messages.error(request, _('This asset is not currently assigned.'))
        return redirect('assets:asset_detail', pk=asset.pk)
    
    if request.method == 'POST':
        with transaction.atomic():
            current_assignment.returned_date = datetime.datetime.now()
            current_assignment.returned_by = request.user
            current_assignment.return_notes = request.POST.get('return_notes', '')
            current_assignment.save()
            
            # Update asset status
            asset.status = 'available'
            asset.assigned_to = None
            asset.save()
            
            # Log the return
            AuditLog.objects.create(
                user=request.user,
                company=request.user.company,
                action=AuditLog.ActionType.RETURN,
                content_object=asset,
                description=f'Returned asset {asset.asset_number} from {current_assignment.assigned_to.get_display_name()}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                request,
                _('Asset "{}" has been returned successfully.').format(asset.asset_number)
            )
        
        return redirect('assets:asset_detail', pk=asset.pk)
    
    return render(request, 'assets/asset_return.html', {
        'asset': asset,
        'assignment': current_assignment
    })


@login_required
def asset_export_view(request):
    """View for asset export with filters and format selection."""
    if request.method == 'POST':
        form = AssetExportForm(user=request.user, data=request.POST)
        if form.is_valid():
            # Get base queryset
            base_queryset = Asset.objects.filter(company=request.user.company).select_related(
                'category', 'brand', 'model', 'assigned_to', 'current_location'
            )
            
            # Apply filters
            filtered_queryset = form.get_filtered_queryset(base_queryset)
            
            # Get export format and fields
            export_format = form.cleaned_data['export_format']
            include_fields = form.cleaned_data['include_fields']
            
            # Generate appropriate export
            if export_format == 'csv':
                return generate_csv_export(request, filtered_queryset, include_fields)
            elif export_format == 'excel':
                return generate_excel_export(request, filtered_queryset, include_fields)
            elif export_format == 'pdf':
                return generate_pdf_export(request, filtered_queryset, include_fields)
    else:
        form = AssetExportForm(user=request.user)
    
    # Get stats for display
    total_assets = Asset.objects.filter(company=request.user.company).count()
    
    context = {
        'form': form,
        'total_assets': total_assets,
    }
    return render(request, 'assets/asset_export.html', context)


def generate_csv_export(request, queryset, include_fields):
    """Generate CSV export with selected fields."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.date.today()}.csv"'
    
    writer = csv.writer(response)
    
    # Define field mapping
    field_mapping = {
        'asset_number': ('Asset Number', lambda asset: asset.asset_number),
        'category': ('Category', lambda asset: asset.category.name if asset.category else ''),
        'brand': ('Brand', lambda asset: asset.brand.name if asset.brand else ''),
        'model': ('Model', lambda asset: asset.model.name if asset.model else ''),
        'serial_number': ('Serial Number', lambda asset: asset.serial_number or ''),
        'description': ('Description', lambda asset: asset.description or ''),
        'status': ('Status', lambda asset: asset.get_status_display()),
        'current_location': ('Current Location', lambda asset: str(asset.current_location) if asset.current_location else ''),
        'assigned_to': ('Assigned To', lambda asset: asset.assigned_to.get_display_name() if asset.assigned_to else ''),
        'purchase_date': ('Purchase Date', lambda asset: asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else ''),
        'purchase_price': ('Purchase Price', lambda asset: str(asset.purchase_price) if asset.purchase_price else ''),
        'warranty_end_date': ('Warranty End Date', lambda asset: asset.warranty_end_date.strftime('%Y-%m-%d') if asset.warranty_end_date else ''),
        'created_at': ('Created At', lambda asset: asset.created_at.strftime('%Y-%m-%d %H:%M:%S')),
        'updated_at': ('Updated At', lambda asset: asset.updated_at.strftime('%Y-%m-%d %H:%M:%S')),
    }
    
    # Write header
    headers = [field_mapping[field][0] for field in include_fields if field in field_mapping]
    writer.writerow(headers)
    
    # Write data
    for asset in queryset:
        row = [field_mapping[field][1](asset) for field in include_fields if field in field_mapping]
        writer.writerow(row)
    
    # Log the export
    AuditLog.objects.create(
        user=request.user,
        company=request.user.company,
        action=AuditLog.ActionType.EXPORT,
        description=f'Exported {queryset.count()} assets to CSV with filters',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return response


def generate_excel_export(request, queryset, include_fields):
    """Generate Excel export with selected fields."""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        messages.error(request, _('Excel export requires openpyxl package. Please contact administrator.'))
        return redirect('assets:asset_export')
    
    # Create workbook and worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Assets Export"
    
    # Define field mapping (same as CSV)
    field_mapping = {
        'asset_number': ('Asset Number', lambda asset: asset.asset_number),
        'category': ('Category', lambda asset: asset.category.name if asset.category else ''),
        'brand': ('Brand', lambda asset: asset.brand.name if asset.brand else ''),
        'model': ('Model', lambda asset: asset.model.name if asset.model else ''),
        'serial_number': ('Serial Number', lambda asset: asset.serial_number or ''),
        'description': ('Description', lambda asset: asset.description or ''),
        'status': ('Status', lambda asset: asset.get_status_display()),
        'current_location': ('Current Location', lambda asset: str(asset.current_location) if asset.current_location else ''),
        'assigned_to': ('Assigned To', lambda asset: asset.assigned_to.get_display_name() if asset.assigned_to else ''),
        'purchase_date': ('Purchase Date', lambda asset: asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else ''),
        'purchase_price': ('Purchase Price', lambda asset: str(asset.purchase_price) if asset.purchase_price else ''),
        'warranty_end_date': ('Warranty End Date', lambda asset: asset.warranty_end_date.strftime('%Y-%m-%d') if asset.warranty_end_date else ''),
        'created_at': ('Created At', lambda asset: asset.created_at.strftime('%Y-%m-%d %H:%M:%S')),
        'updated_at': ('Updated At', lambda asset: asset.updated_at.strftime('%Y-%m-%d %H:%M:%S')),
    }
    
    # Write headers with formatting
    headers = [field_mapping[field][0] for field in include_fields if field in field_mapping]
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # Write data
    for row, asset in enumerate(queryset, 2):
        for col, field in enumerate(include_fields, 1):
            if field in field_mapping:
                value = field_mapping[field][1](asset)
                ws.cell(row=row, column=col, value=value)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Create response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.date.today()}.xlsx"'
    
    wb.save(response)
    
    # Log the export
    AuditLog.objects.create(
        user=request.user,
        company=request.user.company,
        action=AuditLog.ActionType.EXPORT,
        description=f'Exported {queryset.count()} assets to Excel with filters',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return response


def generate_pdf_export(request, queryset, include_fields):
    """Generate PDF export with selected fields."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        import io
    except ImportError:
        messages.error(request, _('PDF export requires reportlab package. Please contact administrator.'))
        return redirect('assets:asset_export')
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Center
    )
    
    # Content
    content = []
    
    # Title
    title = Paragraph(f"Asset Export Report - {datetime.date.today()}", title_style)
    content.append(title)
    content.append(Spacer(1, 12))
    
    # Summary
    summary = Paragraph(f"Total Assets: {queryset.count()}", styles['Normal'])
    content.append(summary)
    content.append(Spacer(1, 12))
    
    # Field mapping
    field_mapping = {
        'asset_number': ('Asset #', lambda asset: asset.asset_number),
        'category': ('Category', lambda asset: asset.category.name if asset.category else ''),
        'brand': ('Brand', lambda asset: asset.brand.name if asset.brand else ''),
        'model': ('Model', lambda asset: asset.model.name if asset.model else ''),
        'serial_number': ('Serial #', lambda asset: asset.serial_number or ''),
        'status': ('Status', lambda asset: asset.get_status_display()),
        'current_location': ('Location', lambda asset: str(asset.current_location) if asset.current_location else ''),
        'assigned_to': ('Assigned To', lambda asset: asset.assigned_to.get_display_name() if asset.assigned_to else ''),
        'purchase_date': ('Purchase Date', lambda asset: asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else ''),
    }
    
    # Create table data
    headers = [field_mapping[field][0] for field in include_fields if field in field_mapping]
    table_data = [headers]
    
    for asset in queryset[:100]:  # Limit for PDF readability
        row = [field_mapping[field][1](asset) for field in include_fields if field in field_mapping]
        table_data.append(row)
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    content.append(table)
    
    # Build PDF
    doc.build(content)
    
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.date.today()}.pdf"'
    
    # Log the export
    AuditLog.objects.create(
        user=request.user,
        company=request.user.company,
        action=AuditLog.ActionType.EXPORT,
        description=f'Exported {queryset.count()} assets to PDF with filters',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return response


@login_required
def asset_export_csv(request):
    """Export assets to CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.date.today()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Asset Number', 'Category', 'Brand', 'Model', 'Serial Number',
        'Status', 'Current Location', 'Assigned To', 'Purchase Date', 'Purchase Price',
        'Warranty End Date', 'Created At'
    ])
    
    assets = Asset.objects.filter(company=request.user.company).select_related(
        'category', 'brand', 'assigned_to'
    )
    
    for asset in assets:
        writer.writerow([
            asset.asset_number,
            asset.category.name if asset.category else '',
            asset.brand.name if asset.brand else '',
            asset.model.name if asset.model else '',
            asset.serial_number,
            asset.get_status_display(),
            asset.current_location,
            asset.assigned_to.get_display_name() if asset.assigned_to else '',
            asset.purchase_date.strftime('%Y-%m-%d') if asset.purchase_date else '',
            asset.purchase_price,
            asset.warranty_end_date.strftime('%Y-%m-%d') if asset.warranty_end_date else '',
            asset.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Log the export
    AuditLog.objects.create(
        user=request.user,
        company=request.user.company,
        action=AuditLog.ActionType.EXPORT,
        description=f'Exported {assets.count()} assets to CSV',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return response


@login_required
def asset_stats_api(request):
    """API endpoint for asset statistics (for dashboard charts)."""
    company = request.user.company
    
    # Status distribution
    status_stats = {}
    for status, label in Asset.AssetStatus.choices:
        count = Asset.objects.filter(company=company, status=status).count()
        status_stats[status] = {
            'label': label,
            'count': count
        }
    
    # Category distribution
    category_stats = list(
        Asset.objects.filter(company=company)
        .values('category__name')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Location distribution
    location_stats = list(
        Asset.objects.filter(company=company)
        .values('current_location')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )
    
    # Monthly acquisition trend (last 12 months)
    from django.utils import timezone
    from dateutil.relativedelta import relativedelta
    
    monthly_stats = []
    current_date = timezone.now().date()
    
    for i in range(12):
        month_start = current_date - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1) - relativedelta(days=1)
        
        count = Asset.objects.filter(
            company=company,
            created_at__date__gte=month_start,
            created_at__date__lte=month_end
        ).count()
        
        monthly_stats.insert(0, {
            'month': month_start.strftime('%Y-%m'),
            'count': count
        })
    
    return JsonResponse({
        'status_stats': status_stats,
        'category_stats': category_stats,
        'location_stats': location_stats,
        'monthly_stats': monthly_stats
    })


@login_required
def asset_import_view(request):
    """
    Import assets from CSV or Excel files.
    Supports validation, preview, and bulk creation with error handling.
    """
    if request.method == 'POST':
        form = AssetImportForm(request.POST, request.FILES, user=request.user)
        
        if form.is_valid():
            try:
                # Process the uploaded file
                result = process_asset_import(
                    file=form.cleaned_data['file'],
                    company=form.cleaned_data['company'],
                    asset_number_mode=form.cleaned_data['asset_number_mode'],
                    asset_number_prefix=form.cleaned_data.get('asset_number_prefix', ''),
                    duplicate_handling=form.cleaned_data['duplicate_handling'],
                    validate_only=form.cleaned_data['validate_only'],
                    user=request.user
                )
                
                if form.cleaned_data['validate_only']:
                    # Preview mode - show validation results
                    messages.info(request, _('File validation completed. Review the results below.'))
                    return render(request, 'assets/import_preview.html', {
                        'form': form,
                        'result': result,
                        'title': _('Asset Import Preview')
                    })
                else:
                    # Actual import
                    if result['success']:
                        messages.success(
                            request, 
                            _('Successfully imported {count} assets.').format(count=result['imported_count'])
                        )
                        if result['errors']:
                            messages.warning(
                                request,
                                _('Some assets could not be imported. Check the error details below.')
                            )
                        return redirect('assets:asset_list')
                    else:
                        messages.error(request, _('Import failed. Please check the errors below.'))
                        
            except Exception as e:
                messages.error(request, _('Import failed: {error}').format(error=str(e)))
                
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = AssetImportForm(user=request.user)
    
    return render(request, 'assets/import_form.html', {
        'form': form,
        'title': _('Import Assets'),
        'sample_csv_url': reverse('assets:sample_csv'),
    })


def process_asset_import(file, company, asset_number_mode, asset_number_prefix, 
                        duplicate_handling, validate_only, user):
    """
    Process asset import from CSV or Excel file.
    Returns a dictionary with import results and any errors.
    """
    result = {
        'success': False,
        'imported_count': 0,
        'errors': [],
        'warnings': [],
        'processed_assets': []
    }
    
    try:
        # Read file based on extension
        file_extension = file.name.lower().split('.')[-1]
        
        if file_extension == 'csv':
            # Read CSV file
            file_content = file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(file_content))
            data_rows = list(csv_reader)
        else:
            # Read Excel file
            df = pd.read_excel(file)
            data_rows = df.to_dict('records')
        
        # Define required and optional columns
        required_columns = []  # No required columns since asset_number is auto-generated
        optional_columns = [
            'asset_number', 'category', 'brand', 'model', 'serial_number', 'description',
            'purchase_price', 'purchase_date', 'warranty_end_date',
            'current_location', 'status', 'condition', 'notes'
        ]
        
        # Validate file has required columns
        if not data_rows:
            result['errors'].append(_('File is empty or has no data rows.'))
            return result
        
        first_row_keys = list(data_rows[0].keys())
        missing_required = [col for col in required_columns if col not in first_row_keys]
        
        if missing_required:
            result['errors'].append(
                _('Missing required columns: {columns}').format(
                    columns=', '.join(missing_required)
                )
            )
            return result
        
        # Process each row
        imported_count = 0
        
        with transaction.atomic() if not validate_only else transaction.atomic():
            for row_num, row_data in enumerate(data_rows, start=2):  # Start at 2 for Excel row numbers
                try:
                    asset_data = process_asset_row(
                        row_data, row_num, company, asset_number_mode, 
                        asset_number_prefix, duplicate_handling, user
                    )
                    
                    if asset_data['success']:
                        if not validate_only:
                            # Create the asset
                            asset = Asset.objects.create(**asset_data['asset_fields'])
                            imported_count += 1
                            
                            # Log the import action
                            AuditLog.objects.create(
                                content_object=asset,
                                action='created',
                                user=user,
                                changes={'imported': True, 'row_number': row_num}
                            )
                        else:
                            imported_count += 1
                        
                        result['processed_assets'].append({
                            'row_number': row_num,
                            'status': 'success',
                            'asset_number': asset_data['asset_fields'].get('asset_number', 'Auto-generated')
                        })
                    else:
                        result['errors'].extend([
                            f"Row {row_num}: {error}" for error in asset_data['errors']
                        ])
                        result['processed_assets'].append({
                            'row_number': row_num,
                            'status': 'error',
                            'errors': asset_data['errors']
                        })
                        
                except Exception as e:
                    error_msg = f"Row {row_num}: Unexpected error - {str(e)}"
                    result['errors'].append(error_msg)
                    result['processed_assets'].append({
                        'row_number': row_num,
                        'status': 'error',
                        'errors': [str(e)]
                    })
        
        result['imported_count'] = imported_count
        result['success'] = imported_count > 0 or validate_only
        
    except Exception as e:
        result['errors'].append(f"File processing error: {str(e)}")
    
    return result


def process_asset_row(row_data, row_num, company, asset_number_mode, 
                     asset_number_prefix, duplicate_handling, user):
    """
    Process a single row of asset data from import file.
    Returns processed asset data or errors.
    """
    result = {
        'success': False,
        'asset_fields': {},
        'errors': []
    }
    
    try:
        # Basic asset fields
        asset_fields = {
            'company': company,
            'created_by': user,
        }
        
        # Handle asset number (optional - will be auto-generated if not provided)
        if 'asset_number' in row_data and row_data['asset_number']:
            asset_number = str(row_data['asset_number']).strip()
            if asset_number:
                # Apply prefix or mode logic
                if asset_number_mode == 'prefix' and asset_number_prefix:
                    asset_fields['asset_number'] = f"{asset_number_prefix}{asset_number}"
                elif asset_number_mode == 'from_file':
                    asset_fields['asset_number'] = asset_number
                # For 'auto' mode, we leave asset_number empty for auto-generation
        
        # Optional fields with validation
        if 'description' in row_data and row_data['description']:
            asset_fields['description'] = str(row_data['description']).strip()
        
        if 'serial_number' in row_data and row_data['serial_number']:
            serial_number = str(row_data['serial_number']).strip()
            
            # Check for duplicate serial numbers
            if duplicate_handling == 'skip':
                existing_asset = Asset.objects.filter(serial_number=serial_number).first()
                if existing_asset:
                    result['errors'].append(
                        _('Asset with serial number {sn} already exists').format(sn=serial_number)
                    )
                    return result
            
            asset_fields['serial_number'] = serial_number
        
        # Handle category
        if 'category' in row_data and row_data['category']:
            category_name = str(row_data['category']).strip()
            try:
                category = AssetCategory.objects.get(name__iexact=category_name)
                asset_fields['category'] = category
            except AssetCategory.DoesNotExist:
                result['errors'].append(
                    _('Category "{category}" not found').format(category=category_name)
                )
        
        # Handle brand
        if 'brand' in row_data and row_data['brand']:
            brand_name = str(row_data['brand']).strip()
            try:
                brand = AssetBrand.objects.get(name__iexact=brand_name)
                asset_fields['brand'] = brand
            except AssetBrand.DoesNotExist:
                result['errors'].append(
                    _('Brand "{brand}" not found').format(brand=brand_name)
                )
        
        # Handle financial fields
        if 'purchase_price' in row_data and row_data['purchase_price']:
            try:
                price = Decimal(str(row_data['purchase_price']).replace(',', ''))
                asset_fields['purchase_price'] = price
            except (InvalidOperation, ValueError):
                result['errors'].append(
                    _('Invalid purchase price: {price}').format(price=row_data['purchase_price'])
                )
        
        # Handle dates
        for date_field in ['purchase_date', 'warranty_end_date']:
            if date_field in row_data and row_data[date_field]:
                try:
                    if isinstance(row_data[date_field], str):
                        # Try to parse date string
                        date_value = pd.to_datetime(row_data[date_field]).date()
                    else:
                        date_value = row_data[date_field]
                    asset_fields[date_field] = date_value
                except:
                    result['errors'].append(
                        _('Invalid date format for {field}: {value}').format(
                            field=date_field, value=row_data[date_field]
                        )
                    )
        
        # Handle other text fields
        for field in ['model', 'current_location', 'notes']:
            if field in row_data and row_data[field]:
                asset_fields[field] = str(row_data[field]).strip()
        
        # Handle choice fields
        if 'status' in row_data and row_data['status']:
            status = str(row_data['status']).strip().lower()
            status_choices = dict(Asset.AssetStatus.choices)
            status_key = None
            for key, value in status_choices.items():
                if value.lower() == status or key.lower() == status:
                    status_key = key
                    break
            if status_key:
                asset_fields['status'] = status_key
            else:
                result['warnings'].append(
                    f"Unknown status '{row_data['status']}', using default"
                )
        
        if 'condition' in row_data and row_data['condition']:
            condition = str(row_data['condition']).strip().lower()
            condition_choices = dict(Asset.AssetCondition.choices)
            condition_key = None
            for key, value in condition_choices.items():
                if value.lower() == condition or key.lower() == condition:
                    condition_key = key
                    break
            if condition_key:
                asset_fields['condition'] = condition_key
            else:
                result['warnings'].append(
                    f"Unknown condition '{row_data['condition']}', using default"
                )
        
        result['asset_fields'] = asset_fields
        result['success'] = len(result['errors']) == 0
        
    except Exception as e:
        result['errors'].append(f"Processing error: {str(e)}")
    
    return result


@login_required
def download_sample_csv(request):
    """
    Download a sample CSV file for asset import.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="asset_import_sample.csv"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'asset_number', 'category', 'brand', 'model', 'serial_number', 'description',
        'purchase_price', 'purchase_date', 'warranty_end_date', 
        'current_location', 'status', 'condition', 'notes'
    ])
    
    # Write sample data
    writer.writerow([
        'LAPTOP-001', 'Laptop', 'Dell', 'XPS 13 9310', 'DL123456789',
        'High-performance ultrabook for development work', '1200.00', '2024-01-15',
        '2027-01-15', 'IT Department', 'available', 'good', 
        'Includes charger and carrying case'
    ])
    
    writer.writerow([
        '', 'Mobile Device', 'Apple', 'iPhone 14 Pro', 'IP987654321',
        'Company mobile phone for executives', '999.00', '2024-02-01',
        '2025-02-01', 'Executive Office', 'assigned', 'excellent',
        'Space Gray, 256GB storage - asset number will be auto-generated'
    ])
    
    writer.writerow([
        'MON-001', 'Monitor', 'HP', 'E27 G5', 'HP555777999',
        'External monitor for workstations', '299.99', '2024-01-20',
        '2027-01-20', 'Desk 5A', 'available', 'good',
        '1920x1080 resolution, HDMI and DisplayPort'
    ])
    
    return response


# ============================================================================
# Category Management Views
# ============================================================================

class CategoryListView(LoginRequiredMixin, ListView):
    """List view for asset categories."""
    model = AssetCategory
    template_name = 'assets/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(code__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create view for asset categories."""
    model = AssetCategory
    form_class = CategoryForm
    template_name = 'assets/category_form.html'
    success_url = reverse_lazy('assets:category_list')

    def form_valid(self, form):
        messages.success(self.request, _('Category created successfully.'))
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for asset categories."""
    model = AssetCategory
    form_class = CategoryForm
    template_name = 'assets/category_form.html'
    success_url = reverse_lazy('assets:category_list')

    def form_valid(self, form):
        messages.success(self.request, _('Category updated successfully.'))
        return super().form_valid(form)


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for asset categories."""
    model = AssetCategory
    template_name = 'assets/category_confirm_delete.html'
    success_url = reverse_lazy('assets:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('Category deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Brand Management Views
# ============================================================================

class BrandListView(LoginRequiredMixin, ListView):
    """List view for asset brands."""
    model = AssetBrand
    template_name = 'assets/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(code__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class BrandCreateView(LoginRequiredMixin, CreateView):
    """Create view for asset brands."""
    model = AssetBrand
    form_class = BrandForm
    template_name = 'assets/brand_form.html'
    success_url = reverse_lazy('assets:brand_list')

    def form_valid(self, form):
        messages.success(self.request, _('Brand created successfully.'))
        return super().form_valid(form)


class BrandUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for asset brands."""
    model = AssetBrand
    form_class = BrandForm
    template_name = 'assets/brand_form.html'
    success_url = reverse_lazy('assets:brand_list')

    def form_valid(self, form):
        messages.success(self.request, _('Brand updated successfully.'))
        return super().form_valid(form)


class BrandDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for asset brands."""
    model = AssetBrand
    template_name = 'assets/brand_confirm_delete.html'
    success_url = reverse_lazy('assets:brand_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('Brand deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Model Management Views
# ============================================================================

class ModelListView(LoginRequiredMixin, ListView):
    """List view for asset models."""
    model = AssetModel
    template_name = 'assets/model_list.html'
    context_object_name = 'models'
    paginate_by = 20
    ordering = ['brand__name', 'name']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('brand')
        search = self.request.GET.get('search')
        brand_id = self.request.GET.get('brand')
        unit = self.request.GET.get('unit')
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(model_number__icontains=search) |
                Q(brand__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)

        if unit:
            queryset = queryset.filter(unit__iexact=unit)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['brands'] = AssetBrand.objects.filter(is_active=True).order_by('name')
        context['selected_brand'] = self.request.GET.get('brand', '')
        context['selected_unit'] = self.request.GET.get('unit', '')
        context['units'] = AssetModel.objects.exclude(unit='').values_list('unit', flat=True).distinct().order_by('unit')
        return context


class ModelCreateView(LoginRequiredMixin, CreateView):
    """Create view for asset models."""
    model = AssetModel
    form_class = ModelForm
    template_name = 'assets/model_form.html'
    success_url = reverse_lazy('assets:model_list')

    def form_valid(self, form):
        messages.success(self.request, _('Model created successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = AssetBrand.objects.filter(is_active=True).order_by('name')
        return context


class ModelUpdateView(LoginRequiredMixin, UpdateView):
    """Update view for asset models."""
    model = AssetModel
    form_class = ModelForm
    template_name = 'assets/model_form.html'
    success_url = reverse_lazy('assets:model_list')

    def form_valid(self, form):
        messages.success(self.request, _('Model updated successfully.'))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = AssetBrand.objects.filter(is_active=True).order_by('name')
        return context


class ModelDeleteView(LoginRequiredMixin, DeleteView):
    """Delete view for asset models."""
    model = AssetModel
    template_name = 'assets/model_confirm_delete.html'
    success_url = reverse_lazy('assets:model_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _('Model deleted successfully.'))
        return super().delete(request, *args, **kwargs)


# ============================================================================
# Combined Brands & Models Management View
# ============================================================================

@login_required
def brands_models_view(request):
    """Combined view for managing brands and models."""
    search = request.GET.get('search', '').strip()
    brand_id = request.GET.get('brand', '').strip()
    unit = request.GET.get('unit', '').strip()

    models_qs = AssetModel.objects.select_related('brand').order_by('brand__name', 'name')
    if search:
        models_qs = models_qs.filter(
            Q(name__icontains=search)
            | Q(model_number__icontains=search)
            | Q(description__icontains=search)
            | Q(brand__name__icontains=search)
        )
    if brand_id:
        models_qs = models_qs.filter(brand_id=brand_id)
    if unit:
        models_qs = models_qs.filter(unit__iexact=unit)

    brands = AssetBrand.objects.filter(models__in=models_qs).distinct().order_by('name')
    context = {
        'brands': brands,
        'models': models_qs,
        'search_query': search,
        'selected_brand': brand_id,
        'selected_unit': unit,
        'brand_filter_options': AssetBrand.objects.filter(is_active=True).order_by('name'),
        'unit_filter_options': AssetModel.objects.exclude(unit='').values_list('unit', flat=True).distinct().order_by('unit'),
    }
    return render(request, 'assets/brands_models.html', context)
