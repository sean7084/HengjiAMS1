"""
Admin configuration for Accounts app.
Configures Django admin interface for User and UserSession models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin interface for the User model.
    Extends Django's built-in UserAdmin to support additional fields.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_2fa_enabled', 'is_active', 'date_joined')
    list_filter = ('role', 'is_2fa_enabled', 'is_active', 'is_staff', 'is_superuser', 'date_joined', 'language_preference')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions', 'companies', 'divisions')
    
    # Define fieldsets for the admin form
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'profile_image')
        }),
        (_('Role and Access'), {
            'fields': ('role', 'companies', 'divisions')
        }),
        (_('Preferences'), {
            'fields': ('language_preference',)
        }),
        (_('Security'), {
            'fields': ('is_2fa_enabled', 'force_2fa_setup', 'last_login_ip')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Define fieldsets for adding new users
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login', 'last_login_ip')


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for UserSession model.
    """
    list_display = ('user', 'ip_address', 'created_at', 'last_activity', 'is_active')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address', 'session_key')
    ordering = ('-created_at',)
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    
    fieldsets = (
        (_('Session Info'), {
            'fields': ('user', 'session_key', 'ip_address', 'user_agent')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_activity')
        }),
    )


# Configure admin site headers
admin.site.site_header = _('HengJi Asset Management System')
admin.site.site_title = _('HengJi AMS Admin')
admin.site.index_title = _('Welcome to HengJi AMS Administration')
