"""
Models for HengJi AMS Products App.
Product pricing information extending AssetBrand and AssetModel.
"""
from django.db import models
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

    class Meta:
        verbose_name = _('Product Price')
        verbose_name_plural = _('Product Prices')
        ordering = ['brand__name', 'model__name']
        unique_together = ['brand', 'model']

    def __str__(self):
        return f"{self.brand.name} - {self.model.name} ({self.price_with_tax})"

    def save(self, *args, **kwargs):
        # Auto-calculate price_with_tax if not set
        if self.price_without_tax and self.tax_rate and not self.price_with_tax:
            self.price_with_tax = self.price_without_tax * (1 + self.tax_rate / 100)
        super().save(*args, **kwargs)

    def get_display_price(self):
        """Return formatted price string."""
        if self.price_with_tax:
            return f"¥{self.price_with_tax:,.2f}"
        return f"¥{self.price_without_tax:,.2f}"
