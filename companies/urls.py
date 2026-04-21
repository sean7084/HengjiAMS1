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
    path('import/csv/', views.company_import_csv_view, name='company_import_csv'),
    path('import/csv/rollback/', views.company_import_rollback_view, name='company_import_rollback'),
    path('import/sample.csv', views.company_import_sample_csv_view, name='company_import_sample_csv'),
    path('<int:pk>/edit/', views.CompanyUpdateView.as_view(), name='company_edit'),
    path('<int:pk>/delete/', views.CompanyDeleteView.as_view(), name='company_delete'),
    
    # Location management
    path('locations/', views.LocationListView.as_view(), name='location_list'),
    path('locations/create/', views.LocationCreateView.as_view(), name='location_create'),
    path('locations/company-contacts/', views.location_company_contacts_api_view, name='location_company_contacts_api'),
    path('locations/import/csv/', views.location_import_csv_view, name='location_import_csv'),
    path('locations/import/csv/rollback/', views.location_import_rollback_view, name='location_import_rollback'),
    path('locations/import/sample.csv', views.location_import_sample_csv_view, name='location_import_sample_csv'),
    path('locations/<int:pk>/edit/', views.LocationUpdateView.as_view(), name='location_edit'),
    path('locations/<int:pk>/delete/', views.LocationDeleteView.as_view(), name='location_delete'),
    
    # Company user management
    path('users/', views.CompanyUserListView.as_view(), name='companyuser_list'),
    path('users/create/', views.CompanyUserCreateView.as_view(), name='companyuser_create'),
    path('users/import/csv/', views.company_contact_import_csv_view, name='company_contact_import_csv'),
    path('users/import/csv/rollback/', views.company_contact_import_rollback_view, name='company_contact_import_rollback'),
    path('users/import/sample.csv', views.company_contact_import_sample_csv_view, name='company_contact_import_sample_csv'),
    path('users/<int:pk>/edit/', views.CompanyUserUpdateView.as_view(), name='companyuser_edit'),
    path('users/<int:pk>/remove/', views.company_contact_remove_view, name='companyuser_remove'),
]
