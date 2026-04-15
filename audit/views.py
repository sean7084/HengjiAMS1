"""
Views for Audit app.
Provides audit log, asset audit, and system event management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
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


class AssetAuditListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing asset audits.
    """
    model = AssetAudit
    template_name = 'audit/assetaudit_list.html'
    context_object_name = 'asset_audits'
    paginate_by = 20
    
    def test_func(self):
        return self.request.user.can_view_audit()
    
    def get_queryset(self):
        queryset = AssetAudit.objects.select_related('primary_auditor', 'company').all()
        
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
        context['title'] = _('Asset Audit Management')
        context['search'] = self.request.GET.get('search', '')
        return context


class AssetAuditCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating new asset audits.
    """
    model = AssetAudit
    form_class = AssetAuditForm
    template_name = 'audit/assetaudit_form.html'
    success_url = reverse_lazy('audit:assetaudit_list')
    
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
        return context


class AssetAuditUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating existing asset audits.
    """
    model = AssetAudit
    form_class = AssetAuditForm
    template_name = 'audit/assetaudit_form.html'
    success_url = reverse_lazy('audit:assetaudit_list')
    
    def test_func(self):
        audit = self.get_object()
        return self.request.user.can_edit_audit(audit)
    
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
        return context
