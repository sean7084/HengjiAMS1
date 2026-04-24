"""
URL configuration for audit app.
Handles audit logging, system events, and asset auditing.
Only includes views that are currently implemented.
"""
from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    # System Events (current implementation)
    path('events/', views.SystemEventListView.as_view(), name='system_event_list'),
    
    # Asset Audits (current implementation)
    path('dashboard/', views.AssetAuditDashboardView.as_view(), name='assetaudit_dashboard'),
    path('new/', views.AssetAuditCreateView.as_view(), name='assetaudit_new'),
    path('history/', views.AssetAuditHistoryView.as_view(), name='assetaudit_history'),
    path('assetaudit/<uuid:pk>/', views.AssetAuditDetailView.as_view(), name='assetaudit_detail'),
    path('assetaudit/<uuid:pk>/edit/', views.AssetAuditUpdateView.as_view(), name='assetaudit_update'),
]
