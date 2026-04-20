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
            'primary_contact_company_user', 'status', 'logo', 'asset_prefix'
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
            'primary_contact_company_user': forms.Select(attrs={
                'class': 'form-select'
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['primary_contact_company_user'].required = False
        self.fields['primary_contact_company_user'].empty_label = _('Select primary contact (optional)')

        if self.instance.pk:
            self.fields['primary_contact_company_user'].queryset = self.instance.company_users.filter(
                status=CompanyUser.UserStatus.ACTIVE
            ).select_related('user').order_by('user__first_name', 'user__last_name', 'user__username')
        else:
            self.fields['primary_contact_company_user'].queryset = CompanyUser.objects.none()

    def clean_primary_contact_company_user(self):
        contact = self.cleaned_data.get('primary_contact_company_user')
        if contact and self.instance.pk and contact.company_id != self.instance.pk:
            raise forms.ValidationError(_('Selected contact must belong to this company.'))
        return contact


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
            'company', 'name', 'code', 'zone', 'rack', 'shelf', 'description',
            'parent_location', 'location_type', 'status', 'area_size',
            'capacity', 'address_line1', 'address_line2', 'city',
            'state_province', 'postal_code', 'country'
        ]
        widgets = {
            'company': forms.Select(attrs={
                'class': 'form-select',
                'required': True
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
            'zone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Zone range (e.g., Z1-Z2)')
            }),
            'rack': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Rack range (e.g., R1-R3)')
            }),
            'shelf': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Shelf range (e.g., S1-S4)')
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

        # Filter parent locations based on selected company.
        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['parent_location'].queryset = Location.objects.filter(company_id=company_id)
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.company:
            self.fields['parent_location'].queryset = Location.objects.filter(
                company=self.instance.company
            ).exclude(pk=self.instance.pk)
        else:
            self.fields['parent_location'].queryset = Location.objects.none()

        self.fields['parent_location'].empty_label = _('Select parent location (optional)')

        self.fields['zone'].required = False
        self.fields['rack'].required = False
        self.fields['shelf'].required = False
        self.fields['zone'].help_text = _('Warehouse only. Supports ranges like Z1-Z2, Z4.')
        self.fields['rack'].help_text = _('Warehouse only. Supports ranges like R1-R3.')
        self.fields['shelf'].help_text = _('Warehouse only. Supports ranges like S1-S4.')

    def clean(self):
        cleaned_data = super().clean()
        location_type = cleaned_data.get('location_type')

        if location_type != Location.LocationType.WAREHOUSE:
            cleaned_data['zone'] = None
            cleaned_data['rack'] = None
            cleaned_data['shelf'] = None

        return cleaned_data


class CompanyUserForm(forms.ModelForm):
    """Form for adding users to a company."""

    class Meta:
        model = CompanyUser
        fields = ['user', 'company', 'role', 'location', 'status', 'employee_id', 'department', 'job_title', 'work_phone', 'work_email']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'company': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'work_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['location'].required = False
        self.fields['location'].empty_label = _('Select location (optional)')
        self.fields['user'].queryset = self.fields['user'].queryset.order_by('first_name', 'last_name', 'username')
        self.fields['company'].queryset = Company.objects.filter(status=Company.CompanyStatus.ACTIVE).order_by('name')

        if 'company' in self.data:
            try:
                company_id = int(self.data.get('company'))
                self.fields['location'].queryset = Location.objects.filter(
                    company_id=company_id,
                    status=Location.LocationStatus.ACTIVE,
                ).order_by('name')
            except (TypeError, ValueError):
                self.fields['location'].queryset = Location.objects.none()
        elif self.instance.pk:
            self.fields['location'].queryset = Location.objects.filter(
                company=self.instance.company,
                status=Location.LocationStatus.ACTIVE,
            ).order_by('name')
        else:
            self.fields['location'].queryset = Location.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        company = cleaned_data.get('company')
        location = cleaned_data.get('location')

        if company and location and location.company_id != company.id:
            self.add_error('location', _('Selected location must belong to the selected company.'))

        return cleaned_data
