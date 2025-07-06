"""
Admin configuration for Reports app.
Configures Django admin interface for Report-related models.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import ReportTemplate, GeneratedReport, ReportSchedule, ReportShare


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for ReportTemplate model.
    """
    list_display = ('name', 'code', 'report_type', 'output_format', 'is_public', 'is_active')
    list_filter = ('report_type', 'output_format', 'is_public', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (_('Template Information'), {
            'fields': ('name', 'code', 'description', 'report_type')
        }),
        (_('Configuration'), {
            'fields': ('output_format', 'template_definition', 'default_filters')
        }),
        (_('Access Control'), {
            'fields': ('is_public', 'allowed_roles')
        }),
        (_('Settings'), {
            'fields': ('is_active', 'requires_approval', 'can_be_scheduled')
        }),
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at')


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    """
    Admin interface for GeneratedReport model.
    """
    list_display = ('report_number', 'name', 'template', 'status', 'requested_by', 'company', 'requested_at')
    list_filter = ('status', 'generation_method', 'output_format', 'company', 'requested_at')
    search_fields = ('report_number', 'name', 'template__name', 'requested_by__username')
    ordering = ('-requested_at',)
    filter_horizontal = ('shared_with',)
    
    fieldsets = (
        (_('Report Information'), {
            'fields': ('report_number', 'name', 'template', 'output_format')
        }),
        (_('Generation Details'), {
            'fields': ('status', 'generation_method', 'filters_applied')
        }),
        (_('Timing'), {
            'fields': ('requested_at', 'started_at', 'completed_at')
        }),
        (_('File Information'), {
            'fields': ('file_path', 'file_size', 'record_count')
        }),
        (_('Organization'), {
            'fields': ('requested_by', 'company')
        }),
        (_('Access Control'), {
            'fields': ('is_public', 'shared_with')
        }),
        (_('Approval'), {
            'fields': ('requires_approval', 'approved', 'approved_by', 'approved_at')
        }),
        (_('Other'), {
            'fields': ('error_message', 'expires_at', 'notes')
        }),
    )
    
    readonly_fields = ('requested_at', 'started_at', 'completed_at', 'file_size', 'record_count')
    
    def get_file_size_display(self, obj):
        """Display file size in human-readable format."""
        return obj.get_file_size_display()
    
    get_file_size_display.short_description = _('File Size')


@admin.register(ReportSchedule)
class ReportScheduleAdmin(admin.ModelAdmin):
    """
    Admin interface for ReportSchedule model.
    """
    list_display = ('name', 'template', 'frequency', 'status', 'company', 'next_run', 'last_run')
    list_filter = ('frequency', 'status', 'company', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'template__name')
    ordering = ('name',)
    filter_horizontal = ('auditors',) if hasattr(ReportSchedule, 'auditors') else ()
    
    fieldsets = (
        (_('Schedule Information'), {
            'fields': ('name', 'description', 'template', 'company')
        }),
        (_('Schedule Configuration'), {
            'fields': ('frequency', 'start_date', 'end_date', 'next_run', 'last_run')
        }),
        (_('Report Parameters'), {
            'fields': ('filters', 'output_format')
        }),
        (_('Distribution'), {
            'fields': ('email_recipients', 'email_subject', 'email_body')
        }),
        (_('Status and Control'), {
            'fields': ('status', 'is_active')
        }),
        (_('Error Handling'), {
            'fields': ('consecutive_failures', 'max_failures', 'last_error')
        }),
    )
    
    readonly_fields = ('created_by', 'created_at', 'updated_at', 'next_run', 'last_run', 'consecutive_failures')


@admin.register(ReportShare)
class ReportShareAdmin(admin.ModelAdmin):
    """
    Admin interface for ReportShare model.
    """
    list_display = ('report', 'shared_with', 'share_type', 'shared_by', 'shared_at', 'access_count')
    list_filter = ('share_type', 'can_reshare', 'shared_at', 'accessed_at')
    search_fields = ('report__report_number', 'shared_with__username', 'shared_by__username')
    ordering = ('-shared_at',)
    
    fieldsets = (
        (_('Share Information'), {
            'fields': ('report', 'shared_with', 'share_type')
        }),
        (_('Configuration'), {
            'fields': ('can_reshare', 'expires_at')
        }),
        (_('Tracking'), {
            'fields': ('shared_by', 'shared_at', 'accessed_at', 'access_count')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )
    
    readonly_fields = ('shared_at', 'accessed_at', 'access_count')
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly for existing objects."""
        readonly_fields = list(self.readonly_fields)
        if obj:  # Editing an existing object
            readonly_fields.extend(['report', 'shared_with', 'shared_by'])
        return readonly_fields
