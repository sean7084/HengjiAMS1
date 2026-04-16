"""
Models for HengJi AMS Customers App.
Customer profile extending Company with delivery and contact information.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from companies.models import Company


class CustomerProfile(models.Model):
    """
    Customer profile extending Company model.
    Adds delivery information and contact fields for quotation workflow.
    """

    class DeliveryMethod(models.TextChoices):
        SELF_PICKUP = 'self_pickup', _('Self Pickup')
        DELIVERY = 'delivery', _('Delivery')
        COURIER = 'courier', _('Courier')
        EXPRESS = 'express', _('Express')

    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='customer_profile',
        verbose_name=_('Company')
    )

    # Contact fields
    contact_person = models.CharField(
        max_length=200,
        verbose_name=_('Contact Person'),
        help_text=_('Primary contact person name')
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Phone'),
        help_text=_('Primary contact phone number')
    )
    email = models.EmailField(
        verbose_name=_('Email'),
        help_text=_('Primary contact email')
    )

    # Delivery address
    delivery_address = models.TextField(
        verbose_name=_('Delivery Address'),
        help_text=_('Detailed delivery address')
    )
    delivery_city = models.CharField(
        max_length=100,
        verbose_name=_('Delivery City')
    )
    delivery_contact = models.CharField(
        max_length=200,
        verbose_name=_('Delivery Contact Name'),
        help_text=_('Name of person to receive delivery')
    )
    delivery_phone = models.CharField(
        max_length=20,
        verbose_name=_('Delivery Phone'),
        help_text=_('Phone number for delivery contact')
    )
    delivery_method = models.CharField(
        max_length=20,
        choices=DeliveryMethod.choices,
        default=DeliveryMethod.DELIVERY,
        verbose_name=_('Delivery Method')
    )

    # Billing
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Tax ID'),
        help_text=_('Tax identification number')
    )

    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Customer Profile')
        verbose_name_plural = _('Customer Profiles')

    def __str__(self):
        return f"{self.company.name} - {self.contact_person}"

    def get_delivery_info_display(self):
        """Return formatted delivery information."""
        return f"{self.delivery_contact} - {self.delivery_phone}\n{self.delivery_address}, {self.delivery_city}"
