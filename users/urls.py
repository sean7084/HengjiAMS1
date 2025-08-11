"""
URL configuration for Users app.
"""
from django.urls import path
from django.views.generic import RedirectView

app_name = 'users'

urlpatterns = [
    # Redirect to accounts app for user management
    path('', RedirectView.as_view(url='/accounts/users/', permanent=False), name='user_list'),
]
