"""
Forms for Customers app.
"""
from django import forms
from .models import CustomerProfile


class CustomerProfileForm(forms.ModelForm):
    """Form for creating and editing CustomerProfile."""

    class Meta:
        model = CustomerProfile
        fields = ['contact_person', 'phone', 'email', 'delivery_address', 'delivery_city',
                  'delivery_contact', 'delivery_phone', 'delivery_method', 'tax_id', 'notes']
        widgets = {
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'delivery_city': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_method': forms.Select(attrs={'class': 'form-select'}),
            'tax_id': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
