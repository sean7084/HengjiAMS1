"""
Admin configuration for Companies app.
Configures Django admin interface for Company and Division models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company, Division, Location, CompanyUser


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """
    Admin interface for Company model.
    """
    list_display = ('name', 'code', 'email', 'phone_number', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'country')
    search_fields = ('name', 'code', 'email', 'phone_number', 'city')
    ordering = ('name',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'description')
        }),
        (_('Contact Information'), {
            'fields': ('email', 'phone_number', 'website')
        }),
        (_('Address'), {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country')
        }),
        (_('Asset Numbering'), {
            'fields': ('asset_prefix', 'next_asset_number')
        }),
        (_('Settings'), {
            'fields': ('status', 'logo')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


class DivisionInline(admin.TabularInline):
    """
    Inline admin for Division model within Company admin.
    """
    model = Division
    extra = 0
    fields = ('name', 'code', 'manager', 'location', 'status')


class CompanyUserInline(admin.TabularInline):
    """
    Inline admin for CompanyUser model within Company admin.
    """
    model = CompanyUser
    extra = 0
    fields = ('user', 'role', 'division', 'location', 'employee_id', 'status')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'division', 'location')


# Add inlines to CompanyAdmin
CompanyAdmin.inlines = [DivisionInline, CompanyUserInline]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    """
    Admin interface for Division model.
    """
    list_display = ('name', 'code', 'company', 'manager', 'location', 'budget_code', 'status')
    list_filter = ('company', 'status', 'created_at')
    search_fields = ('name', 'code', 'company__name', 'manager__username', 'budget_code')
    ordering = ('company__name', 'name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'name', 'code', 'description')
        }),
        (_('Management'), {
            'fields': ('manager', 'location', 'building', 'floor', 'room')
        }),
        (_('Financial'), {
            'fields': ('budget_code',)
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# Location admin
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    """
    Admin interface for Location model.
    """
    list_display = ('name', 'code', 'company', 'division', 'location_type', 'manager', 'status')
    list_filter = ('company', 'division', 'location_type', 'status', 'created_at')
    search_fields = ('name', 'code', 'company__name', 'division__name', 'manager__username', 'city')
    ordering = ('company__name', 'name')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('company', 'division', 'name', 'code', 'description')
        }),
        (_('Type and Hierarchy'), {
            'fields': ('location_type', 'parent_location', 'manager')
        }),
        (_('Physical Details'), {
            'fields': ('area_size', 'capacity')
        }),
        (_('Address'), {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country')
        }),
        (_('Contact'), {
            'fields': ('phone_number', 'email')
        }),
        (_('Coordinates'), {
            'fields': ('latitude', 'longitude')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CompanyUser)
class CompanyUserAdmin(admin.ModelAdmin):
    """
    Admin interface for CompanyUser model.
    """
    list_display = ('user', 'company', 'role', 'department', 'job_title', 'status', 'start_date')
    list_filter = ('company', 'role', 'status', 'division', 'start_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email', 
                    'company__name', 'employee_id', 'department', 'job_title')
    ordering = ('company__name', 'user__last_name', 'user__first_name')
    
    fieldsets = (
        (_('User & Company'), {
            'fields': ('user', 'company', 'role', 'status')
        }),
        (_('Work Assignment'), {
            'fields': ('division', 'location', 'department', 'job_title', 'manager')
        }),
        (_('Employee Details'), {
            'fields': ('employee_id', 'hire_date', 'start_date', 'end_date')
        }),
        (_('Contact Information'), {
            'fields': ('work_phone', 'work_email')
        }),
    )
    
    readonly_fields = ('start_date', 'created_at', 'updated_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'company', 'division', 'location')
