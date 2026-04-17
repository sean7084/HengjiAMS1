"""
Admin configuration for Quotations app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Quotation, QuotationItem, QuotationAttachment


class QuotationItemInline(admin.TabularInline):
    model = QuotationItem
    extra = 0
    readonly_fields = ('brand_name', 'product_description', 'line_total_without_tax', 'line_total_with_tax', 'created_at')
    fields = ('product_price', 'quantity', 'unit_price', 'tax_rate', 'price_without_tax', 'tax_amount', 'line_total_without_tax')


class QuotationAttachmentInline(admin.TabularInline):
    model = QuotationAttachment
    extra = 0
    fields = ('attachment_type', 'file', 'notes', 'uploaded_at')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    """Admin interface for Quotation model."""
    list_display = ('quotation_number', 'customer', 'quotation_date', 'valid_until', 'status', 'total_with_tax', 'created_at')
    list_filter = ('status', 'quotation_date', 'created_at')
    search_fields = ('quotation_number', 'customer__name', 'attn')
    readonly_fields = ('id', 'quotation_number', 'total_without_tax', 'total_tax', 'total_with_tax', 'created_at', 'updated_at')
    inlines = [QuotationItemInline, QuotationAttachmentInline]
    date_hierarchy = 'quotation_date'

    fieldsets = (
        (_('Quotation Info'), {
            'fields': ('id', 'quotation_number', 'customer', 'status')
        }),
        (_('Dates'), {
            'fields': ('quotation_date', 'valid_until')
        }),
        (_('Contact'), {
            'fields': ('attn', 'tel')
        }),
        (_('Totals'), {
            'fields': ('total_without_tax', 'total_tax', 'total_with_tax'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(QuotationItem)
class QuotationItemAdmin(admin.ModelAdmin):
    """Admin interface for QuotationItem model."""
    list_display = ('quotation', 'brand_name', 'product_description', 'quantity', 'unit_price', 'line_total_without_tax')
    list_filter = ('quotation__status', 'created_at')
    search_fields = ('quotation__quotation_number', 'brand_name', 'product_description')
    readonly_fields = ('id', 'price_without_tax', 'tax_amount', 'line_total_without_tax', 'line_total_with_tax', 'created_at')


@admin.register(QuotationAttachment)
class QuotationAttachmentAdmin(admin.ModelAdmin):
    """Admin interface for QuotationAttachment model."""
    list_display = ('quotation', 'attachment_type', 'file', 'uploaded_at')
    list_filter = ('attachment_type', 'uploaded_at')
    search_fields = ('quotation__quotation_number',)
    readonly_fields = ('id', 'uploaded_at')
