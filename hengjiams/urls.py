"""
URL configuration for hengjiams project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import RedirectView

# Non-internationalized URLs (API, admin, etc.)
urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Media files (development only)
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
    
    # Static files (development only)
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),
    
    # Language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

# Internationalized URLs
urlpatterns += i18n_patterns(
    # Dashboard URLs
    path('dashboard/', include('dashboard.urls')),
    
    # Home page redirect to dashboard
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    
    # Authentication URLs
    path('accounts/', include('accounts.urls')),
    
    # Main application URLs
    path('assets/', include('assets.urls')),
    path('companies/', include('companies.urls')),
    path('audit/', include('audit.urls')),
    path('reports/', include('reports.urls')),
    path('users/', include('users.urls')),
    
    # Login/logout shortcuts
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False)),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=False)),
    
    prefix_default_language=False,  # Don't prefix default language
)
