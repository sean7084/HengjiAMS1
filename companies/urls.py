"""
URL configuration for companies app.
Handles company, division, and location management URLs.
"""
from django.urls import path
from . import views

app_name = 'companies'

urlpatterns = [
    # Company Management
    path('', views.CompanyListView.as_view(), name='company_list'),
    path('create/', views.CompanyCreateView.as_view(), name='company_create'),
    path('<uuid:pk>/', views.CompanyDetailView.as_view(), name='company_detail'),
    path('<uuid:pk>/edit/', views.CompanyEditView.as_view(), name='company_edit'),
    path('<uuid:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
    # Division Management
    path('<uuid:company_pk>/divisions/', views.DivisionListView.as_view(), name='division_list'),
    path('<uuid:company_pk>/divisions/create/', views.DivisionCreateView.as_view(), name='division_create'),
    path('divisions/<uuid:pk>/', views.DivisionDetailView.as_view(), name='division_detail'),
    path('divisions/<uuid:pk>/edit/', views.DivisionEditView.as_view(), name='division_edit'),
    path('divisions/<uuid:pk>/delete/', views.DivisionDeleteView.as_view(), name='division_delete'),
    
    # Location Management
    path('<uuid:company_pk>/locations/', views.LocationListView.as_view(), name='location_list'),
    path('<uuid:company_pk>/locations/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('locations/<uuid:pk>/', views.LocationDetailView.as_view(), name='location_detail'),
    path('locations/<uuid:pk>/edit/', views.LocationEditView.as_view(), name='location_edit'),
    path('locations/<uuid:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    
    # Organizational Dashboard
    path('dashboard/', views.OrganizationDashboardView.as_view(), name='organization_dashboard'),
    
    # API endpoints
    path('api/divisions/<uuid:company_pk>/', views.DivisionAPIView.as_view(), name='division_api'),
    path('api/locations/<uuid:company_pk>/', views.LocationAPIView.as_view(), name='location_api'),
]
