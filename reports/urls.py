"""
URL configuration for Reports App.
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Report dashboard
    path('', views.ReportDashboardView.as_view(), name='dashboard'),

    # Asset inventory report with filtering
    path('inventory/', views.AssetInventoryReportView.as_view(), name='asset_inventory'),

    # Chart data APIs (return JSON)
    path('charts/status/', views.AssetStatusChartView.as_view(), name='chart_status'),
    path('charts/category/', views.AssetCategoryChartView.as_view(), name='chart_category'),
    path('charts/brand/', views.AssetBrandChartView.as_view(), name='chart_brand'),
    path('charts/warranty/', views.WarrantyStatusChartView.as_view(), name='chart_warranty'),

    # Quick stats
    path('quick-stats/', views.QuickStatsView.as_view(), name='quick_stats'),
]
