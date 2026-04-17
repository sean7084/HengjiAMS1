"""
URL configuration for HengJi AMS REST API.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, CompanyViewSet, LocationViewSet,
    AssetCategoryViewSet, AssetBrandViewSet, AssetModelViewSet,
    AssetViewSet, AssetAssignmentViewSet, AssetMaintenanceViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'categories', AssetCategoryViewSet, basename='category')
router.register(r'brands', AssetBrandViewSet, basename='brand')
router.register(r'models', AssetModelViewSet, basename='model')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'assignments', AssetAssignmentViewSet, basename='assignment')
router.register(r'maintenance', AssetMaintenanceViewSet, basename='maintenance')

urlpatterns = [
    path('', include(router.urls)),
]
