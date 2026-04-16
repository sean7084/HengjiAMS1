"""
Admin configuration for Purchases app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PurchaseOrder, PurchaseOrderItem, PurchaseReceipt


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0
    readonly_fields = ('quotation_item', 'quantity_ordered', 'quantity_received', 'created_at')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseOrder model."""
    list_display = ('po_number', 'quotation', 'status', 'total_items', 'total_received', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('po_number', 'quotation__quotation_number', 'quotation__customer__name')
    readonly_fields = ('po_number', 'total_items', 'total_received', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseOrderItem model."""
    list_display = ('purchase_order', 'product_description', 'quantity_ordered', 'quantity_received', 'quantity_remaining')
    list_filter = ('purchase_order__status',)
    search_fields = ('purchase_order__po_number', 'product_description')
    readonly_fields = ('created_at',)


@admin.register(PurchaseReceipt)
class PurchaseReceiptAdmin(admin.ModelAdmin):
    """Admin interface for PurchaseReceipt model."""
    list_display = ('receipt_number', 'purchase_order', 'quotation', 'receipt_date', 'status', 'received_by', 'received_count')
    list_filter = ('status', 'receipt_date')
    search_fields = ('receipt_number', 'purchase_order__po_number', 'quotation__quotation_number', 'received_by')
    readonly_fields = ('id', 'receipt_number', 'created_at', 'updated_at')
