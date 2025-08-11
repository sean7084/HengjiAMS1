"""
Admin configuration for Assets app.
Configures Django admin interface for Asset-related models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    AssetCategory, AssetBrand, AssetModel, Asset, AssetAssignment, AssetMaintenance
)


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetCategory model.
    """
    list_display = ('name', 'code', 'parent', 'default_depreciation_years', 'is_active')
    list_filter = ('parent', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'description', 'parent')
        }),
        (_('Settings'), {
            'fields': ('default_depreciation_years', 'icon', 'color')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AssetBrand)
class AssetBrandAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetBrand model.
    """
    list_display = ('name', 'code', 'website', 'support_email', 'default_warranty_years', 'is_active')
    list_filter = ('is_active', 'created_at', 'default_warranty_years')
    search_fields = ('name', 'code', 'website', 'support_email')
    ordering = ('name',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'logo')
        }),
        (_('Contact Information'), {
            'fields': ('website', 'support_email', 'support_phone')
        }),
        (_('Settings'), {
            'fields': ('default_warranty_years',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


# class AssetPhotoInline(admin.TabularInline):
#     """
#     Inline admin for AssetPhoto model.
#     """
#     model = AssetPhoto
#     extra = 0
#     fields = ('photo', 'caption', 'uploaded_by')
#     readonly_fields = ('uploaded_by', 'uploaded_at')


# class AssetDocumentInline(admin.TabularInline):
#     """
#     Inline admin for AssetDocument model.
#     """
#     model = AssetDocument
    extra = 0
    fields = ('document_type', 'title', 'file', 'uploaded_by')
    readonly_fields = ('uploaded_by', 'uploaded_at')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """
    Admin interface for Asset model.
    """
    list_display = ('asset_number', 'name', 'category', 'brand', 'status', 'condition', 'assigned_to', 'company')
    list_filter = ('status', 'condition', 'category', 'brand', 'company', 'created_at')
    search_fields = ('asset_number', 'name', 'serial_number', 'barcode', 'model')
    ordering = ('asset_number',)
    
    fieldsets = (
        (_('Asset Identification'), {
            'fields': ('asset_number', 'name', 'serial_number', 'barcode', 'description')
        }),
        (_('Classification'), {
            'fields': ('category', 'brand', 'model')
        }),
        (_('Financial Information'), {
            'fields': ('purchase_price', 'current_value', 'purchase_date', 'depreciation_years')
        }),
        (_('Warranty'), {
            'fields': ('warranty_start_date', 'warranty_end_date', 'warranty_provider')
        }),
        (_('Status and Condition'), {
            'fields': ('status', 'condition')
        }),
        (_('Organization'), {
            'fields': ('company', 'division', 'location')
        }),
        (_('Assignment'), {
            'fields': ('assigned_to', 'assigned_date')
        }),
        (_('Photos and Documentation'), {
            'fields': ('primary_photo',)
        }),
        (_('Purchase Details'), {
            'fields': ('supplier', 'purchase_order')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    # inlines = [AssetPhotoInline, AssetDocumentInline]
    
    def get_queryset(self, request):
        """
        Optimize queryset with related objects.
        """
        return super().get_queryset(request).select_related(
            'category', 'brand', 'company', 'division', 'location', 'assigned_to'
        )


@admin.register(AssetModel)
class AssetModelAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetModel model.
    """
    list_display = ('name', 'brand', 'model_number', 'is_active', 'created_at')
    list_filter = ('brand', 'is_active', 'created_at')
    search_fields = ('name', 'model_number', 'brand__name')
    ordering = ['brand__name', 'name']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'brand', 'model_number', 'description')
        }),
        (_('Specifications'), {
            'fields': ('specifications',)
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetAssignment model.
    """
    list_display = ('asset', 'assigned_to', 'assigned_by', 'assigned_date', 'returned_date', 'is_active')
    list_filter = ('assigned_date', 'returned_date', 'condition_at_assignment')
    search_fields = ('asset__asset_number', 'assigned_to__username', 'assigned_by__username')
    ordering = ('-assigned_date',)
    
    fieldsets = (
        (_('Assignment Details'), {
            'fields': ('asset', 'assigned_to', 'assigned_by', 'assigned_date')
        }),
        (_('Return Details'), {
            'fields': ('returned_date', 'returned_by')
        }),
        (_('Condition'), {
            'fields': ('condition_at_assignment', 'condition_at_return')
        }),
        (_('Notes'), {
            'fields': ('assignment_notes', 'return_notes')
        }),
    )
    
    readonly_fields = ('assigned_date',)
    
    def is_active(self, obj):
        """Display whether the assignment is currently active."""
        return obj.returned_date is None
    is_active.boolean = True
    is_active.short_description = _('Active')


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetMaintenance model.
    """
    list_display = ('asset', 'maintenance_type', 'status', 'scheduled_date', 'assigned_to', 'cost')
    list_filter = ('maintenance_type', 'status', 'scheduled_date', 'completed_date')
    search_fields = ('asset__asset_number', 'description', 'vendor')
    ordering = ('-scheduled_date',)
    
    fieldsets = (
        (_('Maintenance Details'), {
            'fields': ('asset', 'maintenance_type', 'description', 'priority')
        }),
        (_('Scheduling'), {
            'fields': ('scheduled_date', 'completed_date', 'assigned_to', 'vendor')
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Cost'), {
            'fields': ('cost', 'cost_currency')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at')
