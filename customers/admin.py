"""
Admin configuration for Customers app.
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import CustomerProfile


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    """Admin interface for CustomerProfile model."""
    list_display = ('company', 'contact_person', 'phone', 'email', 'delivery_city', 'delivery_method', 'created_at')
    list_filter = ('delivery_method', 'created_at')
    search_fields = ('company__name', 'contact_person', 'email', 'delivery_city')
    readonly_fields = ('id', 'created_at', 'updated_at')
    raw_id_fields = ('company',)

    fieldsets = (
        (_('Company'), {
            'fields': ('company',)
        }),
        (_('Contact Information'), {
            'fields': ('contact_person', 'phone', 'email')
        }),
        (_('Delivery Address'), {
            'fields': ('delivery_address', 'delivery_city', 'delivery_contact', 'delivery_phone', 'delivery_method')
        }),
        (_('Billing'), {
            'fields': ('tax_id',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
        (_('Metadata'), {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
