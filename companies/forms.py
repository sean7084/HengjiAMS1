"""
Forms for Companies app.
Provides forms for company, division, location, and company user management.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Company, Division, Location, CompanyUser


class CompanyForm(forms.ModelForm):
    """
    Form for creating and updating companies.
    """
    
    class Meta:
        model = Company
        fields = [
            'name', 'code', 'description', 'phone_number', 'email', 'website',
            'address_line1', 'address_line2', 'city', 'state_province',
            'postal_code', 'country', 'status', 'logo', 'asset_prefix'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter company name'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter company code (e.g., HENGJI)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter company description')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+1234567890')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('company@example.com')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('https://www.company.com')
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Street address')
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Apartment, suite, etc. (optional)')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City')
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State/Province')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal/ZIP code')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Country')
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'asset_prefix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Asset numbering prefix (e.g., COMP-)')
            })
        }


class DivisionForm(forms.ModelForm):
    """
    Form for creating and updating divisions.
    """
    
    class Meta:
        model = Division
        fields = [
            'company', 'name', 'code', 'description', 'parent_division',
            'manager', 'phone_number', 'email', 'location', 'building',
            'floor', 'room', 'status', 'budget_code'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter division name'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter division code (optional, e.g., IT, HR, FIN)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter division description')
            }),
            'parent_division': forms.Select(attrs={
                'class': 'form-select'
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+1234567890')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('division@company.com')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter location')
            }),
            'building': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Building name or number')
            }),
            'floor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Floor number')
            }),
            'room': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Room number')
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'budget_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Budget or cost center code')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter parent divisions based on selected company
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['parent_division'].queryset = Division.objects.filter(company_id=company_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.company:
            self.fields['parent_division'].queryset = Division.objects.filter(
                company=self.instance.company
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent_division'].queryset = Division.objects.none()
        
        # Filter managers to users with appropriate roles
        self.fields['manager'].queryset = self.fields['manager'].queryset.filter(
            admin_role__in=['superadmin', 'it_administrator']
        )
        self.fields['manager'].empty_label = _('Select manager (optional)')
        
        # Make code field explicitly optional
        self.fields['code'].required = False
        self.fields['code'].help_text = _('Optional: Unique identifier code for the division within the company')


class LocationForm(forms.ModelForm):
    """
    Form for creating and updating locations.
    """
    
    class Meta:
        model = Location
        fields = [
            'company', 'division', 'name', 'code', 'description',
            'parent_location', 'location_type', 'status', 'area_size',
            'capacity', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'division': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter location name'),
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter location code (e.g., B1-F3-R101)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter location description')
            }),
            'parent_location': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'area_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Area in square meters'),
                'step': '0.01'
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Maximum capacity')
            }),
            'address_line1': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Address line 1')
            }),
            'address_line2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Address line 2 (optional)')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City')
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State/Province')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal code')
            }),
            'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Country')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter divisions based on selected company
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['division'].queryset = Division.objects.filter(company_id=company_id)
                self.fields['parent_location'].queryset = Location.objects.filter(company_id=company_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.company:
            self.fields['division'].queryset = Division.objects.filter(
                company=self.instance.company
            )
            self.fields['parent_location'].queryset = Location.objects.filter(
                company=self.instance.company
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['division'].queryset = Division.objects.none()
            self.fields['parent_location'].queryset = Location.objects.none()
        
        # Set empty labels
        self.fields['division'].empty_label = _('Select division (optional)')
        self.fields['parent_location'].empty_label = _('Select parent location (optional)')
