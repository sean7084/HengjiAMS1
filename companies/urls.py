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
    path('add/', views.CompanyCreateView.as_view(), name='company_create'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_edit'),
    path('<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
    # Location management
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    path('locations/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', views.LocationUpdateView.as_view(), name='location_edit'),
    path('locations/<int:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    
    # Company user management
    path('users/', views.CompanyUserListView.as_view(), name='companyuser_list'),
    path('users/create/', views.CompanyUserCreateView.as_view(), name='companyuser_create'),
    path('users/<int:pk>/edit/', views.CompanyUserUpdateView.as_view(), name='companyuser_edit'),
]
