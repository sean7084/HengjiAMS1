"""
Admin configuration for Assets app.
Simple admin interface for asset management models.
"""
from django.contrib import admin
from .models import AssetCategory, AssetBrand, Asset, AssetAssignment, AssetMaintenance


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    """Admin interface for AssetCategory model."""
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(AssetBrand)
class AssetBrandAdmin(admin.ModelAdmin):
    """Admin interface for AssetBrand model."""
    list_display = ('name', 'code', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin interface for Asset model."""
    list_display = ('asset_number', 'category', 'brand', 'status', 'serial_number', 'created_at')
    list_filter = ('status', 'category', 'brand', 'created_at')
    search_fields = ('asset_number', 'serial_number', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(AssetAssignment)
class AssetAssignmentAdmin(admin.ModelAdmin):
    """Admin interface for AssetAssignment model."""
    list_display = ('asset', 'assigned_to', 'assigned_date', 'returned_date')
    list_filter = ('assigned_date', 'returned_date')
    search_fields = ('asset__asset_number', 'assigned_to__username')
    readonly_fields = ('id', 'assigned_date')


@admin.register(AssetMaintenance)
class AssetMaintenanceAdmin(admin.ModelAdmin):
    """Admin interface for AssetMaintenance model."""
    list_display = ('asset', 'maintenance_type', 'status', 'scheduled_date', 'completed_date')
    list_filter = ('maintenance_type', 'status', 'scheduled_date')
    search_fields = ('asset__asset_number', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')
