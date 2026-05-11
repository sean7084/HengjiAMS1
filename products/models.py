"""
Models for HengJi AMS Products App.
Product and service pricing information for the unified catalog.
"""
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

from assets.models import AssetBrand, AssetModel


class ServiceItem(models.Model):
    """Catalog entry for non-asset service offerings."""

    service_group = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Service Group')
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_('Service Name')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    unit = models.CharField(
        max_length=50,
        default='JOB',
        verbose_name=_('Unit')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Service Item')
        verbose_name_plural = _('Service Items')
        ordering = ['service_group', 'name']

    def __str__(self):
        if self.service_group:
            return f"{self.service_group} - {self.name}"
        return self.name


class ProductPrice(models.Model):
    """
    Unified price-list entry for hardware models and service items.
    """
    brand = models.ForeignKey(
        AssetBrand,
        on_delete=models.CASCADE,
        related_name='product_prices',
        null=True,
        blank=True,
        verbose_name=_('Brand')
    )
    model = models.ForeignKey(
        AssetModel,
        on_delete=models.CASCADE,
        related_name='product_prices',
        null=True,
        blank=True,
        verbose_name=_('Model')
    )
    service_item = models.ForeignKey(
        ServiceItem,
        on_delete=models.CASCADE,
        related_name='product_prices',
        null=True,
        blank=True,
        verbose_name=_('Service Item')
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
        'service_item_id',
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
        ordering = ['service_item__name', 'brand__name', 'model__name', '-is_current', '-valid_from', '-updated_at']
        constraints = [
            models.CheckConstraint(
                check=(
                    (Q(model__isnull=False) & Q(service_item__isnull=True)) |
                    (Q(model__isnull=True) & Q(service_item__isnull=False))
                ),
                name='productprice_single_catalog_target',
            ),
            models.UniqueConstraint(
                fields=['model'],
                condition=Q(is_current=True, model__isnull=False),
                name='uniq_current_product_price_per_model',
            ),
            models.UniqueConstraint(
                fields=['service_item'],
                condition=Q(is_current=True, service_item__isnull=False),
                name='uniq_current_product_price_per_service_item',
            ),
        ]

    def __str__(self):
        return f"{self.display_label} ({self.price_with_tax or self.price_without_tax})"

    @property
    def is_service(self):
        return bool(self.service_item_id)

    @property
    def catalog_type(self):
        return 'service' if self.is_service else 'hardware'

    @property
    def display_brand_name(self):
        if self.is_service:
            return self.service_item.service_group or 'Service'
        if self.brand_id:
            return self.brand.name
        return ''

    @property
    def display_name(self):
        if self.is_service:
            return self.service_item.name
        if self.model_id:
            return self.model.name
        return ''

    @property
    def display_description(self):
        if self.is_service:
            return self.service_item.description or self.service_item.name
        if self.model_id:
            return self.model.description or self.model.name
        return ''

    @property
    def display_model_number(self):
        if self.is_service:
            return ''
        if self.model_id:
            return self.model.model_number or ''
        return ''

    @property
    def display_unit(self):
        if self.unit:
            return self.unit
        if self.is_service:
            return self.service_item.unit or 'JOB'
        if self.model_id:
            return self.model.unit or 'PCS'
        return 'PCS'

    @property
    def display_label(self):
        if self.is_service:
            return f"Service - {self.service_item.name}"
        if self.brand_id and self.model_id:
            return f"{self.brand.name} - {self.model.name}"
        return self.display_name

    def clean(self):
        super().clean()
        if bool(self.model_id) == bool(self.service_item_id):
            raise ValidationError('Select either a hardware model or a service item.')

    def _history_snapshot_required(self, previous):
        return previous.is_current and any(
            getattr(previous, field_name) != getattr(self, field_name)
            for field_name in self.HISTORY_TRACKED_FIELDS
        )

    def _create_history_snapshot(self, previous):
        ProductPrice.objects.create(
            brand=previous.brand,
            model=previous.model,
            service_item=previous.service_item,
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
            self.service_item = None
            self.brand = self.model.brand
            self.unit = self.model.unit or self.unit or 'PCS'
        elif self.service_item_id:
            self.model = None
            self.brand = None
            self.unit = self.service_item.unit or self.unit or 'JOB'

        if self.price_without_tax is not None and self.tax_rate is not None:
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
