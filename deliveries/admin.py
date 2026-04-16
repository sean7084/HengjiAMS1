"""Admin for deliveries app."""

from django.contrib import admin

from .models import DeliveryOrder, DeliveryItem


class DeliveryItemInline(admin.TabularInline):
    model = DeliveryItem
    extra = 0
    readonly_fields = (
        'asset',
        'serial_number',
        'brand_name',
        'product_description',
        'user_brand',
        'user_name',
    )


@admin.register(DeliveryOrder)
class DeliveryOrderAdmin(admin.ModelAdmin):
    list_display = (
        'delivery_number',
        'quotation',
        'delivery_date',
        'receiver_name',
        'status',
        'created_at',
    )
    list_filter = ('status', 'delivery_date', 'created_at')
    search_fields = (
        'delivery_number',
        'quotation__quotation_number',
        'quotation__customer__name',
        'receiver_name',
    )
    readonly_fields = ('delivery_number', 'created_at', 'updated_at')
    inlines = [DeliveryItemInline]


@admin.register(DeliveryItem)
class DeliveryItemAdmin(admin.ModelAdmin):
    list_display = ('delivery_order', 'asset', 'serial_number', 'brand_name', 'quantity')
    list_filter = ('delivery_order__status',)
    search_fields = (
        'delivery_order__delivery_number',
        'asset__asset_number',
        'serial_number',
        'brand_name',
    )
