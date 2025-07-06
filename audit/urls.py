"""
URL configuration for audit app.
Handles audit, compliance, and change tracking URLs.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # Audit Management
    path('', views.AuditListView.as_view(), name='audit_list'),
    path('create/', views.AuditCreateView.as_view(), name='audit_create'),
    path('<uuid:pk>/', views.AuditDetailView.as_view(), name='audit_detail'),
    path('<uuid:pk>/edit/', views.AuditEditView.as_view(), name='audit_edit'),
    path('<uuid:pk>/delete/', views.AuditDeleteView.as_view(), name='audit_delete'),
    
    # Audit Execution
    path('<uuid:pk>/start/', views.AuditStartView.as_view(), name='audit_start'),
    path('<uuid:pk>/complete/', views.AuditCompleteView.as_view(), name='audit_complete'),
    path('<uuid:pk>/report/', views.AuditReportView.as_view(), name='audit_report'),
    
    # Asset Verification
    path('<uuid:audit_pk>/verify/', views.AssetVerificationView.as_view(), name='asset_verification'),
    path('<uuid:audit_pk>/verify/<uuid:asset_pk>/', views.AssetVerifyView.as_view(), name='asset_verify'),
    path('records/<uuid:pk>/', views.AuditRecordDetailView.as_view(), name='audit_record_detail'),
    path('records/<uuid:pk>/edit/', views.AuditRecordEditView.as_view(), name='audit_record_edit'),
    
    # Mobile Audit Interface
    path('mobile/', views.AuditMobileView.as_view(), name='audit_mobile'),
    path('mobile/<uuid:audit_pk>/', views.AuditMobileDetailView.as_view(), name='audit_mobile_detail'),
    
    # Audit Logs and History
    path('logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('logs/<uuid:pk>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    path('change-logs/', views.ChangeLogListView.as_view(), name='change_log_list'),
    
    # System Events
    path('events/', views.SystemEventListView.as_view(), name='system_event_list'),
    path('events/<uuid:pk>/', views.SystemEventDetailView.as_view(), name='system_event_detail'),
    path('events/<uuid:pk>/resolve/', views.SystemEventResolveView.as_view(), name='system_event_resolve'),
    
    # Compliance and Reporting
    path('compliance/', views.ComplianceReportView.as_view(), name='compliance_report'),
    path('dashboard/', views.AuditDashboardView.as_view(), name='audit_dashboard'),
    
    # API endpoints
    path('api/assets/<uuid:audit_pk>/', views.AuditAssetsAPIView.as_view(), name='audit_assets_api'),
    path('api/verify/', views.AssetVerificationAPIView.as_view(), name='asset_verification_api'),
]
