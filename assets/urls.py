"""
URL configuration for assets app.
Handles asset management, assignment, and tracking URLs.
"""
from django.urls import path
from . import views

app_name = 'assets'

urlpatterns = [
    # Asset List and Management
    path('', views.AssetListView.as_view(), name='asset_list'),
    path('create/', views.AssetCreateView.as_view(), name='asset_create'),
    path('<uuid:pk>/', views.AssetDetailView.as_view(), name='asset_detail'),
    path('<uuid:pk>/edit/', views.AssetEditView.as_view(), name='asset_edit'),
    path('<uuid:pk>/delete/', views.AssetDeleteView.as_view(), name='asset_delete'),
    
    # Asset Assignment
    path('<uuid:pk>/assign/', views.AssetAssignView.as_view(), name='asset_assign'),
    path('<uuid:pk>/return/', views.AssetReturnView.as_view(), name='asset_return'),
    path('<uuid:pk>/assignment-history/', views.AssetAssignmentHistoryView.as_view(), name='asset_assignment_history'),
    
    # Asset Photos and Documents
    path('<uuid:pk>/photos/', views.AssetPhotosView.as_view(), name='asset_photos'),
    path('<uuid:pk>/photos/add/', views.AssetPhotoAddView.as_view(), name='asset_photo_add'),
    path('<uuid:pk>/documents/', views.AssetDocumentsView.as_view(), name='asset_documents'),
    path('<uuid:pk>/documents/add/', views.AssetDocumentAddView.as_view(), name='asset_document_add'),
    
    # Asset Categories
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<uuid:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('categories/<uuid:pk>/edit/', views.CategoryEditView.as_view(), name='category_edit'),
    
    # Asset Brands
    path('brands/', views.BrandListView.as_view(), name='brand_list'),
    path('brands/create/', views.BrandCreateView.as_view(), name='brand_create'),
    path('brands/<uuid:pk>/', views.BrandDetailView.as_view(), name='brand_detail'),
    path('brands/<uuid:pk>/edit/', views.BrandEditView.as_view(), name='brand_edit'),
    
    # Import/Export
    path('import/', views.AssetImportView.as_view(), name='asset_import'),
    path('export/', views.AssetExportView.as_view(), name='asset_export'),
    path('bulk-actions/', views.AssetBulkActionsView.as_view(), name='asset_bulk_actions'),
    
    # Mobile/Barcode Scanning
    path('scan/', views.AssetScanView.as_view(), name='asset_scan'),
    path('mobile/', views.AssetMobileView.as_view(), name='asset_mobile'),
    
    # Analytics and Dashboard
    path('dashboard/', views.AssetDashboardView.as_view(), name='asset_dashboard'),
    path('analytics/', views.AssetAnalyticsView.as_view(), name='asset_analytics'),
    
    # API endpoints for AJAX calls
    path('api/search/', views.AssetSearchAPIView.as_view(), name='asset_search_api'),
    path('api/<uuid:pk>/qr-code/', views.AssetQRCodeAPIView.as_view(), name='asset_qr_code_api'),
]
