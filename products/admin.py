"""
Admin configuration for Products app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ProductPrice


@admin.register(ProductPrice)
class ProductPriceAdmin(admin.ModelAdmin):
    """Admin interface for ProductPrice model."""
    list_display = ('brand', 'model', 'unit', 'price_without_tax', 'price_with_tax', 'tax_rate', 'is_current', 'created_at')
    list_filter = ('brand', 'is_current', 'created_at')
    search_fields = ('brand__name', 'model__name', 'model__model_number')
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_per_page = 50

    fieldsets = (
        (_('Product'), {
            'fields': ('brand', 'model', 'unit')
        }),
        (_('Pricing'), {
            'fields': ('price_without_tax', 'tax_rate', 'price_with_tax')
        }),
        (_('Validity'), {
            'fields': ('is_current', 'valid_from', 'valid_until')
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Metadata'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
