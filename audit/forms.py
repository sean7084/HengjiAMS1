"""
Forms for HengJi Asset Management System - Audit App.
This module defines forms for audit-related functionality including
asset audits, audit logs, and system events.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models import AssetAudit
from companies.models import Company, Division, Location
from assets.models import AssetCategory

User = get_user_model()


class AssetAuditForm(forms.ModelForm):
    """Form for creating and editing asset audits."""
    
    class Meta:
        model = AssetAudit
        fields = [
            'audit_number', 'name', 'description', 'audit_type', 'company',
            'divisions', 'locations', 'categories', 'primary_auditor', 'auditors',
            'planned_start_date', 'planned_end_date'
        ]
        widgets = {
            'audit_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., AUDIT-2025-001')
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Descriptive name for this audit')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Purpose and scope of this audit')
            }),
            'audit_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'company': forms.Select(attrs={
                'class': 'form-select'
            }),
            'divisions': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'locations': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'categories': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'primary_auditor': forms.Select(attrs={
                'class': 'form-select'
            }),
            'auditors': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4'
            }),
            'planned_start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'planned_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter companies based on user permissions
            if user.is_superuser:
                companies = Company.objects.all()
            else:
                companies = user.get_accessible_companies()
            
            self.fields['company'].queryset = companies
            self.fields['primary_auditor'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name', 'username')
            self.fields['auditors'].queryset = User.objects.filter(
                is_active=True
            ).order_by('first_name', 'last_name', 'username')
        
        # Update divisions, locations, and categories based on selected company
        if self.instance and self.instance.company_id:
            company = self.instance.company
            self.fields['divisions'].queryset = Division.objects.filter(company=company)
            self.fields['locations'].queryset = Location.objects.filter(company=company)
        else:
            self.fields['divisions'].queryset = Division.objects.none()
            self.fields['locations'].queryset = Location.objects.none()
        
        # All categories available
        self.fields['categories'].queryset = AssetCategory.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        planned_start_date = cleaned_data.get('planned_start_date')
        planned_end_date = cleaned_data.get('planned_end_date')

        if planned_start_date and planned_end_date:
            if planned_end_date <= planned_start_date:
                raise forms.ValidationError(_('Planned end date must be after start date.'))

        return cleaned_data
