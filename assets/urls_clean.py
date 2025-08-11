"""
URL configuration for assets app.
Handles asset CRUD, assignment, search, and analytics.
Only includes views that are currently implemented.
"""
from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Core Asset CRUD Operations
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('<uuid:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('<uuid:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('<uuid:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    
    # Asset Assignment & Return
    path('<uuid:pk>/assign/', views.asset_assign_view, name='asset_assign'),
    path('<uuid:pk>/return/', views.asset_return_view, name='asset_return'),
    
    # Data Export
    path('export/csv/', views.asset_export_csv, name='asset_export_csv'),
    
    # API Endpoints
    path('api/stats/', views.asset_stats_api, name='asset_stats_api'),
]
