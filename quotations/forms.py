"""
Forms for Quotations app.
"""
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
import datetime

from companies.models import Company
from customers.models import CustomerProfile
from products.models import ProductPrice
from .models import Quotation, QuotationItem, QuotationAttachment


class QuotationForm(forms.ModelForm):
    """Form for creating and editing Quotation."""

    class Meta:
        model = Quotation
        fields = ['customer', 'quotation_date', 'valid_until', 'attn', 'tel', 'status', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'quotation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valid_until': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attn': forms.TextInput(attrs={'class': 'form-control'}),
            'tel': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default validity to 30 days from today
        if not self.instance.pk:
            self.fields['valid_until'].initial = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()

    def clean_customer(self):
        customer = self.cleaned_data.get('customer')
        if customer:
            # Get or create customer profile
            try:
                profile = customer.customer_profile
                # Auto-fill attn/tel if not set
                if not self.cleaned_data.get('attn') and profile.contact_person:
                    self.cleaned_data['attn'] = profile.contact_person
                if not self.cleaned_data.get('tel') and profile.phone:
                    self.cleaned_data['tel'] = profile.phone
            except CustomerProfile.DoesNotExist:
                pass
        return customer


class QuotationItemForm(forms.ModelForm):
    """Form for creating and editing QuotationItem."""

    class Meta:
        model = QuotationItem
        fields = ['product_price', 'quantity', 'user_brand', 'user_name']
        widgets = {
            'product_price': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'user_brand': forms.TextInput(attrs={'class': 'form-control'}),
            'user_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity < 1:
            raise forms.ValidationError('Quantity must be at least 1.')
        return quantity


class QuotationItemFormSet(forms.BaseInlineFormSet):
    """FormSet for QuotationItem inline in Quotation form."""

    def clean(self):
        if any(self.errors):
            return
        # At least one item required
        items = [f for f in self.forms if not f.cleaned_data.get('DELETE', False)]
        if not items:
            raise forms.ValidationError('At least one product is required.')


class QuotationAttachmentForm(forms.ModelForm):
    """Form for uploading QuotationAttachment."""

    class Meta:
        model = QuotationAttachment
        fields = ['attachment_type', 'file', 'notes']
        widgets = {
            'attachment_type': forms.Select(attrs={'class': 'form-select'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
