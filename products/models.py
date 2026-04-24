"""
Models for HengJi AMS Products App.
Product pricing information extending AssetBrand and AssetModel.
"""
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from assets.models import AssetBrand, AssetModel


class ProductPrice(models.Model):
    """
    Product price list model linking brand and model with pricing.
    Extends the existing AssetBrand and AssetModel to avoid duplication.
    """
    brand = models.ForeignKey(
        AssetBrand,
        on_delete=models.CASCADE,
        related_name='product_prices',
        verbose_name=_('Brand')
    )
    model = models.ForeignKey(
        AssetModel,
        on_delete=models.CASCADE,
        related_name='product_prices',
        verbose_name=_('Model')
    )
    unit = models.CharField(
        max_length=50,
        default='PCS',
        verbose_name=_('Unit'),
        help_text=_('Unit of measure (e.g., PCS, SET, KG)')
    )
    price_without_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Price Without Tax')
    )
    price_with_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Price With Tax')
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('13.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name=_('Tax Rate (%)'),
        help_text=_('Tax rate as percentage (e.g., 13.00 for 13%)')
    )
    is_current = models.BooleanField(
        default=True,
        verbose_name=_('Current Price'),
        help_text=_('Whether this is the current active price')
    )
    valid_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Valid From'),
        help_text=_('Date from which this price is valid')
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Valid Until'),
        help_text=_('Date until which this price is valid')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    HISTORY_TRACKED_FIELDS = (
        'model_id',
        'unit',
        'price_without_tax',
        'price_with_tax',
        'tax_rate',
        'is_current',
        'valid_from',
        'valid_until',
        'notes',
    )

    class Meta:
        verbose_name = _('Product Price')
        verbose_name_plural = _('Product Prices')
        ordering = ['brand__name', 'model__name', '-is_current', '-valid_from', '-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['model'],
                condition=Q(is_current=True),
                name='uniq_current_product_price_per_model',
            ),
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.model.name} ({self.price_with_tax})"

    def _history_snapshot_required(self, previous):
        return previous.is_current and any(
            getattr(previous, field_name) != getattr(self, field_name)
            for field_name in self.HISTORY_TRACKED_FIELDS
        )

    def _create_history_snapshot(self, previous):
        ProductPrice.objects.create(
            brand=previous.brand,
            model=previous.model,
            unit=previous.unit,
            price_without_tax=previous.price_without_tax,
            price_with_tax=previous.price_with_tax,
            tax_rate=previous.tax_rate,
            is_current=False,
            valid_from=previous.valid_from,
            valid_until=timezone.localdate(),
            notes=previous.notes,
        )

    def save(self, *args, **kwargs):
        if self.model_id:
            self.brand = self.model.brand
            self.unit = self.model.unit or self.unit or 'PCS'

        if self.price_without_tax and self.tax_rate:
            self.price_with_tax = (self.price_without_tax * (Decimal('1') + (self.tax_rate / Decimal('100')))).quantize(Decimal('0.01'))

        if not self.pk:
            super().save(*args, **kwargs)
            return

        previous = ProductPrice.objects.get(pk=self.pk)
        if not self._history_snapshot_required(previous):
            super().save(*args, **kwargs)
            return

        with transaction.atomic():
            self._create_history_snapshot(previous)
            super().save(*args, **kwargs)

    def get_display_price(self):
        """Return formatted price string."""
        if self.price_with_tax:
            return f"¥{self.price_with_tax:,.2f}"
        return f"¥{self.price_without_tax:,.2f}"
