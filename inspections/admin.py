"""Django admin registration for the inspections app."""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    InspectionDevice,
    InspectionIssue,
    InspectionPhoto,
    StoreInspection,
)


class InspectionDeviceInline(admin.TabularInline):
    model = InspectionDevice
    extra = 0
    fields = (
        'row_order', 'category', 'brand_model', 'sn', 'asset_id_text', 'usage',
        'status', 'photo_required', 'is_new_device', 'collected_at',
    )
    readonly_fields = ('collected_at',)
    show_change_link = True


class InspectionIssueInline(admin.TabularInline):
    model = InspectionIssue
    extra = 0
    fields = ('seq', 'description', 'status', 'photo')


class InspectionPhotoInline(admin.TabularInline):
    model = InspectionPhoto
    extra = 0
    fields = ('kind', 'device', 'sort_index', 'display_name', 'image')


@admin.register(StoreInspection)
class StoreInspectionAdmin(admin.ModelAdmin):
    list_display = (
        'store_label', 'jda_code', 'inspection_date', 'engineer', 'status',
        'get_completion_percentage',
    )
    list_filter = ('status', 'inspection_date', 'company', 'division')
    search_fields = ('store_label', 'jda_code', 'store_name', 'brand_name')
    date_hierarchy = 'inspection_date'
    readonly_fields = ('created_at', 'updated_at', 'report_generated_at', 'signed_at')
    inlines = [InspectionDeviceInline, InspectionIssueInline]
    fieldsets = (
        (None, {
            'fields': (
                'company', 'division', 'location',
                'jda_code', 'brand_name', 'store_name', 'store_label',
                'inspection_date', 'engineer', 'status',
            ),
        }),
        (_('Cover Page'), {
            'fields': (
                'arriving_time', 'leaving_time', 'wifi_coverage',
                'error_setting_fixed_count', 'store_issue_found_count',
                'issue_to_follow_count', 'cover_extras',
            ),
        }),
        (_('Confirmation Page'), {
            'fields': ('wifi_covers_store', 'it_support_rating', 'it_support_comment', 'device_counts'),
        }),
        (_('Signoff'), {
            'fields': ('store_signature', 'engineer_signature', 'signed_at'),
        }),
        (_('Deliverables'), {
            'fields': ('report_file', 'photo_zip', 'report_generated_at'),
        }),
        (_('Metadata'), {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Completion %'), ordering='status')
    def get_completion_percentage(self, obj):
        return f'{obj.get_completion_percentage()}%'


@admin.register(InspectionDevice)
class InspectionDeviceAdmin(admin.ModelAdmin):
    list_display = ('store_inspection', 'category', 'brand_model', 'sn', 'asset_id_text', 'status', 'collected_at')
    list_filter = ('status', 'category', 'is_new_device', 'photo_required')
    search_fields = ('sn', 'asset_id_text', 'brand_model', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('store_inspection', 'asset', 'collected_by')


@admin.register(InspectionPhoto)
class InspectionPhotoAdmin(admin.ModelAdmin):
    list_display = ('store_inspection', 'kind', 'device', 'display_name', 'sort_index', 'captured_at')
    list_filter = ('kind',)
    search_fields = ('display_name',)
    raw_id_fields = ('store_inspection', 'device', 'uploaded_by')


@admin.register(InspectionIssue)
class InspectionIssueAdmin(admin.ModelAdmin):
    list_display = ('store_inspection', 'seq', 'status', 'description')
    list_filter = ('status',)
    search_fields = ('description',)
    raw_id_fields = ('store_inspection', 'photo')
