"""
URL configuration for Mobile App.
"""
from django.urls import path
from . import views

app_name = 'mobile'

urlpatterns = [
    path('', views.MobileDashboardView.as_view(), name='dashboard'),
    path('scan/', views.MobileScanView.as_view(), name='scan'),
]
