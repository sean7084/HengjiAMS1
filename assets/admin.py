"""
Admin configuration for Assets app.
Simple admin interface for asset management models.
"""
from django.contrib import admin
from .models import AssetCategory, AssetBrand, AssetModel, Asset, AssetAssignment, AssetMaintenance, AssetActivityLog, AssetFieldChange


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


@admin.register(AssetModel)
class AssetModelAdmin(admin.ModelAdmin):
    """Admin interface for AssetModel model."""
    list_display = ('name', 'brand', 'category', 'model_number', 'is_active', 'created_at')
    list_filter = ('is_active', 'brand', 'category', 'created_at')
    search_fields = ('name', 'model_number', 'brand__name', 'category__name')
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


class AssetFieldChangeInline(admin.TabularInline):
    model = AssetFieldChange
    extra = 0
    readonly_fields = ('field_name', 'old_value', 'new_value', 'field_type')
    can_delete = False


@admin.register(AssetActivityLog)
class AssetActivityLogAdmin(admin.ModelAdmin):
    """Read-only admin for the asset activity trail."""
    list_display = ('created_at', 'operation', 'asset', 'user', 'company')
    list_filter = ('operation', 'created_at')
    search_fields = ('description', 'asset__asset_number', 'user__username')
    readonly_fields = ('id', 'asset', 'user', 'company', 'operation', 'description',
                       'metadata', 'ip_address', 'user_agent', 'created_at')
    inlines = [AssetFieldChangeInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
