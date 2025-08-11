"""
URL configuration for Dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('quick-stats/', views.quick_stats_view, name='quick_stats'),
]
