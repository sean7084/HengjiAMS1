"""
URL configuration for audit app.
Handles audit logging, system events, and asset auditing.
Only includes views that are currently implemented.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # Audit Logs (current implementation)
    path('logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    
    # System Events (current implementation)
    path('events/', views.SystemEventListView.as_view(), name='system_event_list'),
    
    # Asset Audits (current implementation)
    path('assetaudit/', views.AssetAuditListView.as_view(), name='assetaudit_list'),
    path('assetaudit/create/', views.AssetAuditCreateView.as_view(), name='assetaudit_create'),
    path('assetaudit/<uuid:pk>/', views.AssetAuditDetailView.as_view(), name='assetaudit_detail'),
    path('assetaudit/<uuid:pk>/edit/', views.AssetAuditUpdateView.as_view(), name='assetaudit_update'),
    
    # Legacy audit log management (maintained for backward compatibility)
    path('auditlog/', views.AuditLogListView.as_view(), name='auditlog_list'),
    
    # Legacy system event management (maintained for backward compatibility)
    path('systemevent/', views.SystemEventListView.as_view(), name='systemevent_list'),
    
    # Main audit list (redirect to audit logs for now)
    path('', views.AuditLogListView.as_view(), name='audit_list'),
]
