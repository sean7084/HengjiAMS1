"""
Forms for Products app.
"""
from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from assets.models import AssetModel

from .models import ProductPrice


class ProductPriceForm(forms.ModelForm):
    """Form for creating and editing ProductPrice."""

    brand_name = forms.CharField(
        required=False,
        label='Brand',
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        current_price_model_ids = ProductPrice.objects.filter(is_current=True)
        if self.instance.pk:
            current_price_model_ids = current_price_model_ids.exclude(pk=self.instance.pk)

        self.fields['model'].queryset = AssetModel.objects.filter(is_active=True).exclude(
            pk__in=current_price_model_ids.values_list('model_id', flat=True)
        ).select_related('brand').order_by('brand__name', 'name')
        self.fields['model'].empty_label = _('Select model')
        self.fields['model'].widget.attrs.update({'class': 'form-select'})
        self.fields['unit'].widget.attrs.update({'readonly': 'readonly'})

        if not self.instance.pk and not self.is_bound:
            self.fields['valid_from'].initial = timezone.localdate()

        selected_model = self.instance.model if getattr(self.instance, 'model_id', None) else None
        if selected_model:
            self.fields['brand_name'].initial = selected_model.brand.name
            self.fields['unit'].initial = selected_model.unit
        elif self.data.get('model'):
            try:
                selected_model = self.fields['model'].queryset.get(pk=self.data['model'])
            except (AssetModel.DoesNotExist, ValueError, TypeError):
                selected_model = None

            if selected_model:
                self.fields['brand_name'].initial = selected_model.brand.name
                self.fields['unit'].initial = selected_model.unit

    class Meta:
        model = ProductPrice
        fields = ['model', 'unit', 'price_without_tax', 'tax_rate', 'price_with_tax', 'is_current', 'valid_from', 'valid_until', 'notes']
        widgets = {
            'model': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'price_without_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_with_tax': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'valid_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        selected_model = cleaned_data.get('model')
        price_without_tax = cleaned_data.get('price_without_tax')
        tax_rate = cleaned_data.get('tax_rate')

        if selected_model:
            cleaned_data['unit'] = selected_model.unit or 'PCS'

        if price_without_tax and tax_rate:
            # Auto-calculate price_with_tax
            calculated_price = price_without_tax * (Decimal('1') + (tax_rate / Decimal('100')))
            cleaned_data['price_with_tax'] = calculated_price.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.model_id:
            instance.brand = instance.model.brand
            instance.unit = instance.model.unit or instance.unit or 'PCS'
        if commit:
            instance.save()
            self.save_m2m()
        return instance
