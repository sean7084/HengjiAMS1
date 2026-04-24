"""
Views for Audit app.
Provides audit log, asset audit, and system event management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import AuditLog, SystemEvent, AssetAudit
from .forms import AssetAuditForm
from accounts.models import User


class AuditLogListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing audit logs.
    """
    model = AuditLog
    template_name = 'audit/auditlog_list.html'
    context_object_name = 'audit_logs'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_view_audit()
    
    def get_queryset(self):
        queryset = AuditLog.objects.select_related('user', 'content_type').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(action__icontains=search) |
                Q(description__icontains=search) |
                Q(content_type__model__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Audit Log Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class SystemEventListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing system events.
    """
    model = SystemEvent
    template_name = 'audit/systemevent_list.html'
    context_object_name = 'system_events'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_view_audit()
    
    def get_queryset(self):
        queryset = SystemEvent.objects.all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(event_type__icontains=search) |
                Q(message__icontains=search) |
                Q(source__icontains=search)
            )
        
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('System Event Management')
        context['search'] = self.request.GET.get('search', '')
        return context


def _get_asset_audit_back_url(audit):
    if audit.status in [AssetAudit.AuditStatus.COMPLETED, AssetAudit.AuditStatus.CANCELLED]:
        return reverse('audit:assetaudit_history')
    return reverse('audit:assetaudit_dashboard')


class BaseAssetAuditListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Base view for filtered asset audit listings."""

    model = AssetAudit
    template_name = 'audit/assetaudit_list.html'
    context_object_name = 'asset_audits'
    paginate_by = 20
    page_title = _('Asset Audits')
    current_section = 'dashboard'
    status_filter = None
    empty_title = _('No asset audits found')
    empty_message = _('Create your first asset audit to get started.')
    
    def test_func(self):
        return self.request.user.can_view_audit()
    
    def get_queryset(self):
        queryset = AssetAudit.objects.select_related('primary_auditor', 'company').all()

        if self.status_filter:
            queryset = queryset.filter(status__in=self.status_filter)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(audit_number__icontains=search) |
                Q(name__icontains=search) |
                Q(primary_auditor__username__icontains=search) |
                Q(primary_auditor__first_name__icontains=search) |
                Q(primary_auditor__last_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.page_title
        context['search'] = self.request.GET.get('search', '')
        context['current_section'] = self.current_section
        context['dashboard_url'] = reverse('audit:assetaudit_dashboard')
        context['history_url'] = reverse('audit:assetaudit_history')
        context['new_url'] = reverse('audit:assetaudit_new')
        context['empty_title'] = self.empty_title
        context['empty_message'] = self.empty_message
        return context


class AssetAuditDashboardView(BaseAssetAuditListView):
    """Show planned and in-progress audits."""

    page_title = _('Audit Dashboard')
    current_section = 'dashboard'
    status_filter = [AssetAudit.AuditStatus.PLANNED, AssetAudit.AuditStatus.IN_PROGRESS]
    empty_title = _('No active audits found')
    empty_message = _('Create a new audit to start tracking current audit work.')


class AssetAuditHistoryView(BaseAssetAuditListView):
    """Show completed and cancelled audits."""

    page_title = _('Audit History')
    current_section = 'history'
    status_filter = [AssetAudit.AuditStatus.COMPLETED, AssetAudit.AuditStatus.CANCELLED]
    empty_title = _('No audit history found')
    empty_message = _('Completed and cancelled audits will appear here.')


class AssetAuditCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new asset audits.
    """
    model = AssetAudit
    form_class = AssetAuditForm
    template_name = 'audit/assetaudit_form.html'
    success_url = reverse_lazy('audit:assetaudit_dashboard')
    
    def test_func(self):
        return self.request.user.can_create_audit()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(
            self.request,
            _('Asset audit "{}" has been created successfully.').format(form.instance.name)
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Create New Asset Audit')
        context['submit_text'] = _('Create Audit')
        context['back_url'] = reverse('audit:assetaudit_dashboard')
        return context


class AssetAuditUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating existing asset audits.
    """
    model = AssetAudit
    form_class = AssetAuditForm
    template_name = 'audit/assetaudit_form.html'
    
    def test_func(self):
        audit = self.get_object()
        return self.request.user.can_edit_audit(audit)

    def get_success_url(self):
        return _get_asset_audit_back_url(self.object)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(
            self.request,
            _('Asset audit "{}" has been updated successfully.').format(form.instance.name)
        )
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Asset Audit')
        context['submit_text'] = _('Update Audit')
        context['back_url'] = _get_asset_audit_back_url(self.object)
        return context


class AssetAuditDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    View for displaying asset audit details.
    """
    model = AssetAudit
    template_name = 'audit/assetaudit_detail.html'
    context_object_name = 'audit'
    
    def test_func(self):
        audit = self.get_object()
        return self.request.user.can_view_audit(audit)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Asset Audit Details')
        context['back_url'] = _get_asset_audit_back_url(self.object)
        context['recent_records'] = self.object.records.select_related('asset', 'audited_by').order_by('-audited_at')[:20]
        return context
