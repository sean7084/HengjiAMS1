"""
Forms for Products app.
"""
from django import forms
from .models import ProductPrice


class ProductPriceForm(forms.ModelForm):
    """Form for creating and editing ProductPrice."""

    class Meta:
        model = ProductPrice
        fields = ['brand', 'model', 'unit', 'price_without_tax', 'tax_rate', 'price_with_tax', 'is_current', 'valid_from', 'valid_until', 'notes']
        widgets = {
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'model': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
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
        price_without_tax = cleaned_data.get('price_without_tax')
        tax_rate = cleaned_data.get('tax_rate')

        if price_without_tax and tax_rate:
            # Auto-calculate price_with_tax
            cleaned_data['price_with_tax'] = price_without_tax * (1 + tax_rate / 100)

        return cleaned_data
