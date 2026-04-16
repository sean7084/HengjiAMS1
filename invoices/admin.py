from django.contrib import admin

from .models import EmailDispatch, InvoiceInfo, InvoiceInfoItem, WeeklyOrderBatch, WorkflowStatusAudit


class InvoiceInfoInline(admin.TabularInline):
    model = InvoiceInfo
    extra = 0
    readonly_fields = (
        'invoice_number',
        'invoice_date',
        'kering_group_po_number',
        'internal_order',
        'sap_cost_center',
        'source_row_number',
        'created_at',
        'net_amount',
        'tax_amount',
        'gross_amount',
    )


class InvoiceInfoItemInline(admin.TabularInline):
    model = InvoiceInfoItem
    extra = 0
    readonly_fields = (
        'line_number',
        'description',
        'unit_price',
        'quantity',
        'net_amount',
        'tax_amount',
        'gross_amount',
    )


@admin.register(WeeklyOrderBatch)
class WeeklyOrderBatchAdmin(admin.ModelAdmin):
    list_display = (
        'batch_id',
        'status',
        'total_rows',
        'created_rows',
        'uploaded_at',
        'processed_at',
    )
    list_filter = ('status', 'uploaded_at', 'processed_at')
    search_fields = ('batch_id', 'failure_reason', 'sharepoint_file')
    readonly_fields = (
        'batch_id',
        'uploaded_at',
        'processed_at',
        'total_rows',
        'created_rows',
        'failed_row_number',
        'failure_reason',
    )
    inlines = [InvoiceInfoInline]


@admin.register(InvoiceInfo)
class InvoiceInfoAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'invoice_date',
        'bill_to',
        'kering_group_po_number',
        'internal_order',
        'sap_cost_center',
        'net_amount',
        'tax_amount',
        'gross_amount',
        'weekly_batch',
    )
    list_filter = ('invoice_date', 'tax_rate')
    search_fields = (
        'invoice_number',
        'bill_to',
        'kering_group_po_number',
        'internal_order',
        'sap_cost_center',
        'weekly_batch__batch_id',
    )
    readonly_fields = ('invoice_number', 'created_at', 'updated_at')
    inlines = [InvoiceInfoItemInline]


@admin.register(InvoiceInfoItem)
class InvoiceInfoItemAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_info',
        'line_number',
        'description',
        'unit_price',
        'quantity',
        'gross_amount',
    )
    search_fields = (
        'invoice_info__invoice_number',
        'description',
    )


@admin.register(EmailDispatch)
class EmailDispatchAdmin(admin.ModelAdmin):
    list_display = (
        'quotation',
        'subject',
        'status',
        'sent_to',
        'sent_at',
        'esker_sent',
        'esker_sent_at',
    )
    list_filter = ('status', 'esker_sent', 'sent_at', 'created_at')
    search_fields = (
        'quotation__quotation_number',
        'subject',
        'sent_to',
        'cc',
        'bcc',
    )
    readonly_fields = ('attachments', 'sent_at', 'esker_sent_at', 'created_at', 'updated_at')


@admin.register(WorkflowStatusAudit)
class WorkflowStatusAuditAdmin(admin.ModelAdmin):
    list_display = (
        'entity_type',
        'reference',
        'from_status',
        'to_status',
        'changed_at',
    )
    list_filter = ('entity_type', 'to_status', 'changed_at')
    search_fields = ('entity_type', 'entity_id', 'reference', 'from_status', 'to_status', 'notes')
    readonly_fields = ('entity_type', 'entity_id', 'reference', 'from_status', 'to_status', 'changed_at', 'changed_by', 'notes')
