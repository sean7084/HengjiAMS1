"""
URL configuration for Customers app.
"""
from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerProfileListView.as_view(), name='profile_list'),
    path('<int:company_id>/', views.CustomerProfileDetailView.as_view(), name='profile_detail'),
    path('<int:company_id>/edit/', views.CustomerProfileUpdateView.as_view(), name='profile_edit'),
    path('<int:company_id>/create/', views.CustomerProfileCreateView.as_view(), name='profile_create'),
]
