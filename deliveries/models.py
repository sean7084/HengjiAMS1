"""Models for delivery order workflow."""

import datetime

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class DeliveryOrder(models.Model):
    """Delivery order generated from a quotation."""

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        PREPARED = 'prepared', _('Prepared')
        DISPATCHED = 'dispatched', _('Dispatched')
        COMPLETED = 'completed', _('Completed')

    quotation = models.ForeignKey(
        'quotations.Quotation',
        on_delete=models.PROTECT,
        related_name='delivery_orders',
        verbose_name=_('Source Quotation'),
    )
    delivery_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Delivery Number'),
    )
    delivery_date = models.DateField(
        default=datetime.date.today,
        verbose_name=_('Delivery Date'),
    )

    receiver_name = models.CharField(max_length=200, verbose_name=_('Receiver Name'))
    receiver_phone = models.CharField(max_length=20, verbose_name=_('Receiver Phone'))
    delivery_address = models.TextField(verbose_name=_('Delivery Address'))
    delivery_method = models.CharField(max_length=100, blank=True, verbose_name=_('Delivery Method'))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
    )
    signed_file = models.FileField(
        upload_to='deliveries/signed/%Y/%m/',
        null=True,
        blank=True,
        verbose_name=_('Signed Copy'),
    )
    remarks = models.TextField(blank=True, verbose_name=_('Remarks'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Delivery Order')
        verbose_name_plural = _('Delivery Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['delivery_number']),
            models.Index(fields=['status']),
            models.Index(fields=['delivery_date']),
        ]

    def __str__(self):
        return f"{self.delivery_number} - {self.quotation.quotation_number}"

    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = self.generate_delivery_number()
        super().save(*args, **kwargs)

    def generate_delivery_number(self):
        today = datetime.date.today()
        prefix = f"DO-{today.strftime('%Y%m%d')}-"
        last_order = DeliveryOrder.objects.filter(
            delivery_number__startswith=prefix
        ).order_by('-delivery_number').first()

        if last_order:
            try:
                last_seq = int(last_order.delivery_number.split('-')[-1])
                seq = last_seq + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1

        return f"{prefix}{seq:03d}"


class DeliveryItem(models.Model):
    """Item dispatched in a delivery order, linked to a received asset."""

    delivery_order = models.ForeignKey(
        DeliveryOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Delivery Order'),
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='delivery_items',
        verbose_name=_('Asset'),
    )

    serial_number = models.CharField(max_length=255, blank=True, verbose_name=_('Serial Number'))
    brand_name = models.CharField(max_length=255, blank=True, verbose_name=_('Brand'))
    product_description = models.TextField(blank=True, verbose_name=_('Product Description'))
    user_brand = models.CharField(max_length=255, blank=True, verbose_name=_('User Brand'))
    user_name = models.CharField(max_length=200, blank=True, verbose_name=_('User Name'))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_('Quantity'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Delivery Item')
        verbose_name_plural = _('Delivery Items')
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(
                fields=['delivery_order', 'asset'],
                name='unique_asset_per_delivery_order',
            )
        ]

    def __str__(self):
        return f"{self.delivery_order.delivery_number} - {self.asset.asset_number}"

    def clean(self):
        super().clean()
        if (
            self.asset_id
            and self.delivery_order_id
            and self.asset.source_quotation_id != self.delivery_order.quotation_id
        ):
            raise ValidationError('Selected asset must come from the same source quotation.')

        if self.asset_id and self.delivery_order_id:
            active_statuses = [
                DeliveryOrder.Status.PENDING,
                DeliveryOrder.Status.PREPARED,
                DeliveryOrder.Status.DISPATCHED,
            ]
            conflict_exists = DeliveryItem.objects.filter(
                asset=self.asset,
                delivery_order__status__in=active_statuses,
            ).exclude(delivery_order=self.delivery_order).exists()
            if conflict_exists:
                raise ValidationError('Selected asset is already reserved by another active delivery order.')

    def save(self, *args, **kwargs):
        if self.asset_id:
            self.serial_number = self.asset.serial_number
            self.brand_name = self.asset.brand.name if self.asset.brand else ''
            self.product_description = self.asset.description or ''

            if self.delivery_order_id and self.delivery_order.quotation_id:
                match = self.delivery_order.quotation.items.filter(
                    product_price__brand=self.asset.brand,
                    product_price__model=self.asset.model,
                ).first()
                if match:
                    self.user_brand = match.user_brand
                    self.user_name = match.user_name

        self.full_clean()
        super().save(*args, **kwargs)
