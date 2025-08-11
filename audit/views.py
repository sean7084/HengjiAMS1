"""
Views for Audit app.
Provides audit log, asset audit, and system event management.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from .models import AuditLog, SystemEvent, AssetAudit
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
        queryset = AuditLog.objects.select_related('user').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(action__icontains=search) |
                Q(model_name__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
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
        
        return queryset.order_by('-created_at')
    
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
        queryset = AssetAudit.objects.select_related('asset', 'user').all()
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(asset__name__icontains=search) |
                Q(asset__asset_number__icontains=search) |
                Q(user__username__icontains=search) |
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(notes__icontains=search)
            )
        
        return queryset.order_by('-audit_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Asset Audit Management')
        context['search'] = self.request.GET.get('search', '')
        return context
