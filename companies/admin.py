"""
Admin configuration for Companies app.
Configures Django admin interface for Company and Division models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Company, Division


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
            'fields': ('name', 'code', 'email', 'phone')
        }),
        (_('Address'), {
            'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country')
        }),
        (_('Asset Numbering'), {
            'fields': ('asset_numbering_type', 'asset_prefix', 'next_asset_number')
        }),
        (_('Status'), {
            'fields': ('is_active',)
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


# Add inlines to CompanyAdmin
CompanyAdmin.inlines = [DivisionInline]


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


# Location admin will be added when Location model is implemented
# @admin.register(Location)
# class LocationAdmin(admin.ModelAdmin):
#     """
#     Admin interface for Location model.
#     """
#     list_display = ('name', 'code', 'company', 'division', 'location_type', 'contact_person', 'is_active')
#     list_filter = ('company', 'division', 'location_type', 'is_active', 'created_at')
#     search_fields = ('name', 'code', 'company__name', 'division__name', 'contact_person', 'city')
#     ordering = ('company__name', 'name')
#     
#     fieldsets = (
#         (_('Basic Information'), {
#             'fields': ('company', 'division', 'name', 'code', 'description')
#         }),
#         (_('Type and Contact'), {
#             'fields': ('location_type', 'contact_person', 'contact_phone')
#         }),
#         (_('Address'), {
#             'fields': ('address_line1', 'address_line2', 'city', 'state_province', 'postal_code', 'country')
#         }),
#         (_('Status'), {
#             'fields': ('is_active',)
#         }),
#     )
#     
#     readonly_fields = ('created_at', 'updated_at')
