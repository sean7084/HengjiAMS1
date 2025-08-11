"""
URL configuration for Companies app.
Provides company, division, location, and company user management.
"""
from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company management
    path('', views.CompanyListView.as_view(), name='company_list'),
    
    # Division management
    path('divisions/', views.DivisionListView.as_view(), name='division_list'),
    
    # Location management
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    
    # Company user management
    path('users/', views.CompanyUserListView.as_view(), name='companyuser_list'),
]
