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

from .models import Asset, AssetCategory, AssetBrand, AssetAssignment, AssetMaintenance
from .forms import AssetForm, AssetSearchForm, AssetAssignmentForm
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
        ).select_related('assigned_to', 'assigned_by').order_by('-assigned_at')
        
        # Get maintenance history
        context['maintenance_records'] = AssetMaintenance.objects.filter(
            asset=asset
        ).order_by('-maintenance_date')
        
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
                description=f'Created asset: {self.object.asset_number} - {self.object.name}',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                self.request,
                _('Asset "{}" has been created successfully.').format(self.object.name)
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
                _('Asset "{}" has been updated successfully.').format(self.object.name)
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
                description=f'Deleted (retired) asset: {self.object.asset_number} - {self.object.name}',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(
                request,
                _('Asset "{}" has been retired successfully.').format(self.object.name)
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
                    asset=asset, returned_at__isnull=True
                ).first()
                
                if current_assignment:
                    current_assignment.returned_at = datetime.datetime.now()
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
                        asset.name, assignment.assigned_to.get_display_name()
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
            current_assignment.returned_at = datetime.datetime.now()
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
                _('Asset "{}" has been returned successfully.').format(asset.name)
            )
        
        return redirect('assets:asset_detail', pk=asset.pk)
    
    return render(request, 'assets/asset_return.html', {
        'asset': asset,
        'assignment': current_assignment
    })


@login_required
def asset_export_csv(request):
    """Export assets to CSV file."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="assets_export_{datetime.date.today()}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Asset Number', 'Name', 'Category', 'Brand', 'Model', 'Serial Number',
        'Status', 'Current Location', 'Assigned To', 'Purchase Date', 'Purchase Price',
        'Warranty End Date', 'Created At'
    ])
    
    assets = Asset.objects.filter(company=request.user.company).select_related(
        'category', 'brand', 'assigned_to'
    )
    
    for asset in assets:
        writer.writerow([
            asset.asset_number,
            asset.name,
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
