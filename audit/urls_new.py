"""
URL configuration for Audit app.
Placeholder URLs until views are implemented.
"""
from django.urls import path
from django.views.generic import TemplateView

app_name = 'audit'

urlpatterns = [
    # Placeholder URLs - views to be implemented
    path('', TemplateView.as_view(template_name='coming_soon.html'), name='audit_list'),
]
