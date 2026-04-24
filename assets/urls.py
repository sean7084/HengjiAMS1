"""
URL configuration for assets app.
Handles asset CRUD, assignment, search, analytics, and import functionality.
Only includes views that are currently implemented.
"""
from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Core Asset CRUD Operations
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('bulk-edit/', views.asset_bulk_edit_view, name='asset_bulk_edit'),
    path('logs/', views.AssetChangeLogListView.as_view(), name='asset_log_list'),
    path('logs/<uuid:pk>/', views.AssetChangeLogDetailView.as_view(), name='asset_log_detail'),
    path('<uuid:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('<uuid:pk>/edit/', views.AssetUpdateView.as_view(), name='asset_update'),
    path('<uuid:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    
    # Asset Assignment & Return
    path('<uuid:pk>/assign/', views.asset_assign_view, name='asset_assign'),
    path('<uuid:pk>/return/', views.asset_return_view, name='asset_return'),
    
    # Data Import/Export
    path('import/', views.asset_import_view, name='asset_import'),
    path('import/rollback/', views.asset_import_rollback_view, name='asset_import_rollback'),
    path('import/sample.csv', views.download_sample_csv, name='sample_csv'),
    path('export/', views.asset_export_view, name='asset_export'),
    path('export/csv/', views.asset_export_csv, name='asset_export_csv'),
    
    # Category Management
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<uuid:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<uuid:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
    
    # Brand Management
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<uuid:pk>/edit/', views.BrandUpdateView.as_view(), name='brand_update'),
    path('brands/<uuid:pk>/delete/', views.BrandDeleteView.as_view(), name='brand_delete'),
    
    # Model Management
    path('models/', views.ModelListView.as_view(), name='model_list'),
    path('models/create/', views.ModelCreateView.as_view(), name='model_create'),
    path('models/<uuid:pk>/edit/', views.ModelUpdateView.as_view(), name='model_update'),
    path('models/<uuid:pk>/delete/', views.ModelDeleteView.as_view(), name='model_delete'),
    
    # Combined Brands & Models Management
    path('brands-models/', views.brands_models_view, name='brands_models'),
    
    # API Endpoints
    path('api/stats/', views.asset_stats_api, name='asset_stats_api'),
]
