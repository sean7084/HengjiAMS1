"""
Forms for Quotations app.
"""
from django import forms
from django.core.validators import MinValueValidator
from decimal import Decimal
import datetime

from companies.models import Company
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
        self.fields['customer'].queryset = Company.objects.filter(status=Company.CompanyStatus.ACTIVE).order_by('name')
        # Set default validity to 30 days from today
        if not self.instance.pk:
            self.fields['valid_until'].initial = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
            self.fields['status'].initial = Quotation.QuotationStatus.SENT

    def clean(self):
        cleaned_data = super().clean()
        customer = self.cleaned_data.get('customer')
        if customer:
            contact = customer.primary_contact_company_user
            if contact:
                if not cleaned_data.get('attn'):
                    cleaned_data['attn'] = contact.user.get_display_name()
                if not cleaned_data.get('tel'):
                    cleaned_data['tel'] = contact.work_phone or contact.user.phone_number or ''
        return cleaned_data


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
