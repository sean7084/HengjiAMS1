"""
Admin configuration for Audit app.
Configures Django admin interface for Audit-related models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import AuditLog, AssetAudit, AssetAuditRecord, ChangeLog, SystemEvent


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditLog model.
    """
    list_display = ('user', 'action', 'content_object', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp', 'company')
    search_fields = ('user__username', 'description', 'ip_address')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (_('Action Details'), {
            'fields': ('user', 'action', 'description')
        }),
        (_('Target Object'), {
            'fields': ('content_type', 'object_id')
        }),
        (_('Context'), {
            'fields': ('company', 'ip_address', 'user_agent')
        }),
        (_('Metadata'), {
            'fields': ('metadata',)
        }),
    )
    
    readonly_fields = ('timestamp', 'user', 'action', 'content_type', 'object_id', 
                      'description', 'metadata', 'ip_address', 'user_agent', 'company')
    
    def has_add_permission(self, request):
        """Audit logs should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs should not be deleted."""
        return False


class AssetAuditRecordInline(admin.TabularInline):
    """
    Inline admin for AssetAuditRecord model.
    """
    model = AssetAuditRecord
    extra = 0
    fields = ('asset', 'status', 'audited_by', 'audited_at', 'requires_follow_up')
    readonly_fields = ('audited_at',)


@admin.register(AssetAudit)
class AssetAuditAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetAudit model.
    """
    list_display = ('audit_number', 'name', 'audit_type', 'status', 'company', 'primary_auditor', 'planned_start_date')
    list_filter = ('audit_type', 'status', 'company', 'planned_start_date', 'created_at')
    search_fields = ('audit_number', 'name', 'description', 'primary_auditor__username')
    ordering = ('-created_at',)
    filter_horizontal = ('divisions', 'locations', 'categories', 'auditors')
    
    fieldsets = (
        (_('Audit Information'), {
            'fields': ('audit_number', 'name', 'description', 'audit_type', 'status')
        }),
        (_('Scope'), {
            'fields': ('company', 'divisions', 'locations', 'categories')
        }),
        (_('Auditors'), {
            'fields': ('primary_auditor', 'auditors')
        }),
        (_('Schedule'), {
            'fields': ('planned_start_date', 'planned_end_date', 'actual_start_date', 'actual_end_date')
        }),
        (_('Results'), {
            'fields': ('total_assets_expected', 'total_assets_found', 'total_assets_missing', 'total_discrepancies')
        }),
        (_('Reporting'), {
            'fields': ('report_generated', 'notes')
        }),
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    inlines = [AssetAuditRecordInline]


@admin.register(AssetAuditRecord)
class AssetAuditRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for AssetAuditRecord model.
    """
    list_display = ('audit', 'asset', 'status', 'audited_by', 'audited_at', 'requires_follow_up')
    list_filter = ('status', 'audited_at', 'requires_follow_up', 'follow_up_completed')
    search_fields = ('audit__audit_number', 'asset__asset_number', 'audited_by__username')
    ordering = ('-audited_at',)
    
    fieldsets = (
        (_('Audit Information'), {
            'fields': ('audit', 'asset', 'status', 'audited_by')
        }),
        (_('Physical Verification'), {
            'fields': ('physical_location_verified', 'actual_location')
        }),
        (_('Condition Assessment'), {
            'fields': ('condition_at_audit', 'condition_notes')
        }),
        (_('Asset Information'), {
            'fields': ('serial_number_verified', 'actual_serial_number')
        }),
        (_('Photos'), {
            'fields': ('verification_photo', 'serial_number_photo')
        }),
        (_('Notes and Discrepancies'), {
            'fields': ('notes', 'discrepancies')
        }),
        (_('Follow-up'), {
            'fields': ('requires_follow_up', 'follow_up_assigned_to', 'follow_up_completed')
        }),
    )
    
    readonly_fields = ('audited_at',)


@admin.register(ChangeLog)
class ChangeLogAdmin(admin.ModelAdmin):
    """
    Admin interface for ChangeLog model.
    """
    list_display = ('audit_log', 'field_name', 'old_value', 'new_value')
    list_filter = ('field_name', 'field_type')
    search_fields = ('field_name', 'old_value', 'new_value')
    ordering = ('field_name',)
    
    readonly_fields = ('audit_log', 'field_name', 'old_value', 'new_value', 'field_type')
    
    def has_add_permission(self, request):
        """Change logs should not be manually created."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Change logs should not be modified."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Change logs should not be deleted."""
        return False


@admin.register(SystemEvent)
class SystemEventAdmin(admin.ModelAdmin):
    """
    Admin interface for SystemEvent model.
    """
    list_display = ('event_type', 'category', 'severity', 'user', 'timestamp', 'resolved')
    list_filter = ('category', 'severity', 'resolved', 'timestamp')
    search_fields = ('event_type', 'message', 'user__username')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (_('Event Information'), {
            'fields': ('event_type', 'category', 'severity', 'message')
        }),
        (_('Context'), {
            'fields': ('user', 'ip_address', 'metadata')
        }),
        (_('Resolution'), {
            'fields': ('resolved', 'resolved_by', 'resolved_at', 'resolution_notes')
        }),
    )
    
    readonly_fields = ('timestamp',)
    
    def get_readonly_fields(self, request, obj=None):
        """Make fields readonly for existing objects."""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('event_type', 'category', 'severity', 'message', 'user', 'ip_address', 'metadata')
        return self.readonly_fields
