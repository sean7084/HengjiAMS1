"""
URL configuration for Dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('workflow/', views.workflow_dashboard_view, name='workflow_dashboard'),
    path('workflow/search/', views.workflow_search_view, name='workflow_search'),
    path('quick-stats/', views.quick_stats_view, name='quick_stats'),
    path('save-config/', views.save_dashboard_config, name='save_config'),
]
