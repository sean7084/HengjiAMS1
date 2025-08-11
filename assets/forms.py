"""
Forms for Assets app - Asset Management System.
Provides forms for creating, updating, and searching assets.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models import Asset, AssetCategory, AssetBrand, AssetAssignment
from companies.models import Location, Division

User = get_user_model()


class AssetForm(forms.ModelForm):
    """Form for creating and updating assets."""
    
    class Meta:
        model = Asset
        fields = [
            'name', 'category', 'brand', 'model', 'serial_number',
            'description', 'current_location', 'status', 'purchase_date',
            'purchase_price', 'warranty_provider', 'warranty_end_date',
            'notes', 'photo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter asset name')
            }),
            'model': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter model number/name')
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter serial number')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Enter asset description')
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': _('0.00')
            }),
            'warranty_provider': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter warranty provider')
            }),
            'warranty_end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Additional notes')
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'current_location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter current location')
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and hasattr(self.user, 'company'):
            # Add company filter if needed
            pass
        
        # Make fields required
        self.fields['name'].required = True
        self.fields['category'].required = True
        self.fields['current_location'].required = True
        
        # Add help text
        self.fields['serial_number'].help_text = _('Leave blank for auto-generation')
        self.fields['purchase_price'].help_text = _('Purchase price in company currency')


class AssetSearchForm(forms.Form):
    """Form for searching and filtering assets."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by asset number, name, or serial number'),
            'autofocus': True
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Categories'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    status = forms.ChoiceField(
        choices=[('', _('All Statuses'))] + Asset.AssetStatus.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    order_by = forms.ChoiceField(
        choices=[
            ('-created_at', _('Newest First')),
            ('created_at', _('Oldest First')),
            ('name', _('Name A-Z')),
            ('-name', _('Name Z-A')),
            ('asset_number', _('Asset Number A-Z')),
            ('-asset_number', _('Asset Number Z-A')),
            ('status', _('Status')),
        ],
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class AssetAssignmentForm(forms.ModelForm):
    """Form for assigning assets to users and locations."""
    
    class Meta:
        model = AssetAssignment
        fields = ['assignment_type', 'assigned_to', 'location', 'expected_return_date', 'notes']
        widgets = {
            'assignment_type': forms.Select(attrs={'class': 'form-select'}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.Select(attrs={'class': 'form-select'}),
            'expected_return_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Optional assignment notes')
            })
        }
    
    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        self.fields['assigned_to'].required = False
        self.fields['location'].required = False
        self.fields['expected_return_date'].required = False
        
        # Add JavaScript to handle assignment type changes
        self.fields['assignment_type'].widget.attrs.update({
            'onchange': 'handleAssignmentTypeChange(this.value)'
        })
        
        # Filter users and locations by company if provided
        if company:
            from companies.models import CompanyUser
            company_users = CompanyUser.objects.filter(
                company=company,
                status=CompanyUser.UserStatus.ACTIVE
            ).select_related('user')
            
            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=[cu.user.id for cu in company_users]
            ).order_by('first_name', 'last_name', 'username')
            
            self.fields['location'].queryset = company.locations.filter(
                status=Location.LocationStatus.ACTIVE
            ).order_by('name')
        
        self.fields['assigned_to'].empty_label = _('Select user to assign')
        self.fields['location'].empty_label = _('Select location')


class AssetBulkActionForm(forms.Form):
    """Form for bulk actions on assets."""
    
    ACTION_CHOICES = [
        ('', _('Select Action')),
        ('update_status', _('Update Status')),
        ('assign_user', _('Assign to User')),
        ('export_csv', _('Export to CSV')),
        ('delete', _('Mark as Retired')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Optional fields for specific actions
    status = forms.ChoiceField(
        choices=[('', '')] + Asset.AssetStatus.choices,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'company'):
            self.fields['assigned_to'].queryset = User.objects.filter(
                company=user.company,
                is_active=True
            )


class AssetImportForm(forms.Form):
    """Form for importing assets from CSV/Excel files."""
    
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        }),
        help_text=_('Upload CSV or Excel file with asset data')
    )
    
    update_existing = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text=_('Update existing assets if asset tag matches')
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        
        # Check file extension
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        file_extension = file.name.lower().split('.')[-1]
        if f'.{file_extension}' not in allowed_extensions:
            raise forms.ValidationError(
                _('Invalid file format. Please upload CSV or Excel files only.')
            )
        
        # Check file size (max 10MB)
        if file.size > 10 * 1024 * 1024:
            raise forms.ValidationError(
                _('File too large. Maximum size is 10MB.')
            )
        
        return file


class AssetMaintenanceForm(forms.Form):
    """Form for asset maintenance records."""
    
    MAINTENANCE_TYPE_CHOICES = [
        ('preventive', _('Preventive Maintenance')),
        ('corrective', _('Corrective Maintenance')),
        ('emergency', _('Emergency Repair')),
        ('inspection', _('Inspection')),
        ('calibration', _('Calibration')),
        ('upgrade', _('Upgrade')),
    ]
    
    maintenance_type = forms.ChoiceField(
        choices=MAINTENANCE_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    maintenance_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Describe the maintenance work performed')
        })
    )
    
    cost = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': _('0.00')
        })
    )
    
    performed_by = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Technician or company name')
        })
    )
    
    next_maintenance_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        help_text=_('When is the next maintenance due?')
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Additional notes')
        })
    )
