"""
Forms for Assets app - Asset Management System.
Provides forms for creating, updating, and searching assets.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
import csv
import io

from .models import Asset, AssetCategory, AssetBrand, AssetAssignment, AssetModel
from companies.models import Location, Division, Company

User = get_user_model()


def hardware_category_queryset():
    return AssetCategory.objects.filter(is_active=True).exclude(
        item_type=AssetCategory.ItemType.SERVICE,
    )


def hardware_model_queryset():
    return AssetModel.objects.filter(is_active=True).exclude(
        category__item_type=AssetCategory.ItemType.SERVICE,
    )


def hardware_brand_queryset():
    return AssetBrand.objects.filter(is_active=True).filter(
        Q(models__isnull=True)
        | Q(models__category__isnull=True)
        | Q(models__category__item_type=AssetCategory.ItemType.HARDWARE)
    ).distinct()


class AssetForm(forms.ModelForm):
    """Form for creating and updating assets."""

    location_zone = forms.ChoiceField(
        required=False,
        label=_('Zone'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location_rack = forms.ChoiceField(
        required=False,
        label=_('Rack'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location_shelf = forms.ChoiceField(
        required=False,
        label=_('Shelf'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    amount = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        label=_('Quantity'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1',
        })
    )
    
    class Meta:
        model = Asset
        fields = [
            'asset_number', 'category', 'brand', 'model', 'serial_number',
            'description', 'location', 'location_zone', 'location_rack', 'location_shelf', 'status', 'purchase_date',
            'purchase_price', 'warranty_provider', 'warranty_end_date',
            'notes', 'photo'
        ]
        widgets = {
            'asset_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Leave blank for auto-generation')
            }),
            'model': forms.Select(attrs={'class': 'form-select'}),
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
            'location': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self._location_slot_map = {}

        selected_category_id = ''
        if self.is_bound:
            selected_category_id = self.data.get('category', '')
        elif self.instance.pk and self.instance.category_id:
            selected_category_id = str(self.instance.category_id)
        elif self.initial.get('category'):
            selected_category = self.initial.get('category')
            selected_category_id = str(getattr(selected_category, 'pk', selected_category))
        
        if self.user and hasattr(self.user, 'company'):
            # Add company filter if needed
            pass
        
        category_qs = hardware_category_queryset()
        if self.instance.pk and self.instance.category_id:
            category_qs = AssetCategory.objects.filter(
                Q(pk__in=category_qs.values('pk')) | Q(pk=self.instance.category_id)
            )
        self.fields['category'].queryset = category_qs.order_by('name')

        # Set up model choices with brand information.
        models_qs = hardware_model_queryset().select_related('brand', 'category')
        if self.instance.pk and self.instance.model_id:
            models_qs = AssetModel.objects.filter(
                Q(pk__in=models_qs.values('pk')) | Q(pk=self.instance.model_id)
            ).select_related('brand', 'category')
        models_qs = models_qs.order_by('brand__name', 'name')
        
        # Create custom choices that include brand name in the display
        model_choices = [('', _('Select model'))]
        for model in models_qs:
            try:
                model_choices.append((str(model.pk), f"{model.brand.name} - {model.name}"))
            except AttributeError:
                # Handle case where model might not have a brand
                model_choices.append((str(model.pk), model.name))
        
        self.fields['model'].choices = model_choices
        # Make sure the field is not required (it's optional in the model)
        self.fields['model'].required = False
        self.fields['category'].empty_label = _('Select category')
        self.fields['brand'].empty_label = _('Select brand')

        brand_qs = hardware_brand_queryset()
        if selected_category_id:
            brand_qs = brand_qs.filter(models__is_active=True, models__category_id=selected_category_id).distinct()
        if self.instance.pk and self.instance.brand_id:
            brand_qs = AssetBrand.objects.filter(Q(is_active=True) | Q(pk=self.instance.brand_id)).filter(
                Q(pk__in=brand_qs.values('pk')) | Q(pk=self.instance.brand_id)
            )
        self.fields['brand'].queryset = brand_qs.order_by('name')
        
        # Make required fields
        self.fields['category'].required = True
        self.fields['location'].required = True
        
        if self.user and hasattr(self.user, 'company'):
            company = self.user.company
            # Filter locations by company
            location_qs = Location.objects.filter(company=company, status=Location.LocationStatus.ACTIVE)
            # Fallback to all active locations when company-scoped list is empty.
            if not location_qs.exists():
                location_qs = Location.objects.filter(status=Location.LocationStatus.ACTIVE)
        else:
            # If no company context, show all active locations
            location_qs = Location.objects.filter(status=Location.LocationStatus.ACTIVE)
        
        # Set up location choices
        self.fields['location'].queryset = location_qs.order_by('name')
        self.fields['location'].empty_label = _('Select location')

        def _location_label(location):
            scheme = location.get_naming_scheme()
            if scheme:
                return f"{location.name} ({scheme})"
            if location.code:
                return f"{location.name} ({location.code})"
            return location.name

        self.fields['location'].label_from_instance = _location_label

        self._location_slot_map = self._build_location_slot_map(location_qs)
        selected_location_id = self.data.get('location') if self.is_bound else getattr(self.initial.get('location'), 'pk', self.initial.get('location'))
        if not selected_location_id and self.instance.pk and self.instance.location_id:
            selected_location_id = str(self.instance.location_id)
        self._configure_slot_choices(selected_location_id)

        # Default to Vanke VMO Warehouse on create pages when available.
        if not self.instance.pk and not self.is_bound:
            preferred_location = location_qs.filter(name__iexact='Vanke VMO Warehouse').first()
            if preferred_location:
                self.fields['location'].initial = preferred_location.pk
        
        # If no locations available, make field not required and show helpful message
        if not location_qs.exists():
            self.fields['location'].required = False
            self.fields['location'].help_text = _('No locations available. Please create locations first.')
        
        # Asset number is optional (auto-generated if blank)
        self.fields['asset_number'].required = False
        self.fields['serial_number'].required = False
        
        # Add help text
        self.fields['asset_number'].help_text = _('Leave blank for auto-generation based on company and category')
        self.fields['serial_number'].help_text = _('Leave blank for auto-generation')
        self.fields['purchase_price'].help_text = _('Purchase price in company currency')

    def _build_location_slot_map(self, location_qs):
        slot_map = {}
        for location in location_qs:
            if location.location_type != Location.LocationType.WAREHOUSE:
                continue
            zones = location.expanded_zones()
            racks = location.expanded_racks()
            shelves = location.expanded_shelves()
            slot_map[str(location.pk)] = {
                'zones': zones,
                'racks': racks,
                'shelves': shelves,
            }
        return slot_map

    def _configure_slot_choices(self, selected_location_id):
        selected_key = str(selected_location_id) if selected_location_id else ''
        slot_data = self._location_slot_map.get(selected_key, {})
        zones = slot_data.get('zones', [])
        racks = slot_data.get('racks', [])
        shelves = slot_data.get('shelves', [])

        self.fields['location_zone'].choices = [('', _('Select zone'))] + [(value, value) for value in zones]
        self.fields['location_rack'].choices = [('', _('Select rack'))] + [(value, value) for value in racks]
        self.fields['location_shelf'].choices = [('', _('Select shelf'))] + [(value, value) for value in shelves]

        self.fields['location_zone'].help_text = _('Optional. Choose if you need exact warehouse slot.')
        self.fields['location_rack'].help_text = _('Optional. Choose if you need exact warehouse slot.')
        self.fields['location_shelf'].help_text = _('Optional. Choose if you need exact warehouse slot.')

    def get_location_slot_map(self):
        return self._location_slot_map

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        brand = cleaned_data.get('brand')
        model = cleaned_data.get('model')
        location = cleaned_data.get('location')
        zone = (cleaned_data.get('location_zone') or '').strip()
        rack = (cleaned_data.get('location_rack') or '').strip()
        shelf = (cleaned_data.get('location_shelf') or '').strip()

        if model:
            if brand and model.brand_id != brand.id:
                self.add_error('model', _('Selected model does not belong to selected brand.'))
            if category and model.category_id and model.category_id != category.id:
                self.add_error('model', _('Selected model does not belong to selected category.'))

        if not location:
            return cleaned_data

        if location.location_type != Location.LocationType.WAREHOUSE:
            cleaned_data['location_zone'] = None
            cleaned_data['location_rack'] = None
            cleaned_data['location_shelf'] = None
            return cleaned_data

        zones = set(location.expanded_zones())
        racks = set(location.expanded_racks())
        shelves = set(location.expanded_shelves())

        if not zones or not racks or not shelves:
            raise ValidationError(_('The selected warehouse does not have valid zone/rack/shelf ranges configured.'))

        # Warehouse slot values are optional, but if provided they must be valid.
        if zone and zone not in zones:
            self.add_error('location_zone', _('Please select a valid zone.'))
        if rack and rack not in racks:
            self.add_error('location_rack', _('Please select a valid rack.'))
        if shelf and shelf not in shelves:
            self.add_error('location_shelf', _('Please select a valid shelf.'))

        cleaned_data['location_zone'] = zone or None
        cleaned_data['location_rack'] = rack or None
        cleaned_data['location_shelf'] = shelf or None
        return cleaned_data


class AssetSearchForm(forms.Form):
    """Form for searching and filtering assets."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by asset number or serial number'),
            'autofocus': True
        })
    )


class AssetBulkEditForm(forms.Form):
    """Bulk edit form for applying updates to selected assets."""

    asset_ids = forms.CharField(
        required=True,
        widget=forms.HiddenInput()
    )

    apply_quantity = forms.IntegerField(
        required=False,
        min_value=1,
        label=_('Apply To Quantity'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'step': '1',
            'placeholder': _('All selected')
        })
    )

    category = forms.ModelChoiceField(
        queryset=AssetCategory.objects.filter(is_active=True),
        required=False,
        empty_label=_('No change'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    brand = forms.ModelChoiceField(
        queryset=AssetBrand.objects.filter(is_active=True),
        required=False,
        empty_label=_('No change'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    model = forms.ModelChoiceField(
        queryset=AssetModel.objects.filter(is_active=True).select_related('brand', 'category').order_by('brand__name', 'name'),
        required=False,
        empty_label=_('No change'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location = forms.ModelChoiceField(
        queryset=Location.objects.none(),
        required=False,
        empty_label=_('No change'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location_zone = forms.ChoiceField(
        required=False,
        label=_('Zone'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location_rack = forms.ChoiceField(
        required=False,
        label=_('Rack'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    location_shelf = forms.ChoiceField(
        required=False,
        label=_('Shelf'),
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    status = forms.ChoiceField(
        choices=[('', _('No change'))] + list(Asset.AssetStatus.choices),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    purchase_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    purchase_price = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
    )

    warranty_provider = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('No change')})
    )

    warranty_end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': _('No change')})
    )

    editable_fields = (
        'category', 'brand', 'model', 'location',
        'location_zone', 'location_rack', 'location_shelf',
        'status', 'purchase_date', 'purchase_price',
        'warranty_provider', 'warranty_end_date', 'notes'
    )

    def _set_slot_choices(self, location=None):
        no_change = [('', _('No change'))]
        if not location or location.location_type != Location.LocationType.WAREHOUSE:
            self.fields['location_zone'].choices = no_change
            self.fields['location_rack'].choices = no_change
            self.fields['location_shelf'].choices = no_change
            return

        zones = location.expanded_zones()
        racks = location.expanded_racks()
        shelves = location.expanded_shelves()

        self.fields['location_zone'].choices = no_change + [(value, value) for value in zones]
        self.fields['location_rack'].choices = no_change + [(value, value) for value in racks]
        self.fields['location_shelf'].choices = no_change + [(value, value) for value in shelves]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = hardware_category_queryset().order_by('name')
        self.fields['brand'].queryset = hardware_brand_queryset().order_by('name')
        self.fields['model'].queryset = hardware_model_queryset().select_related('brand', 'category').order_by('brand__name', 'name')

        location_qs = Location.objects.filter(status=Location.LocationStatus.ACTIVE)
        if self.user and hasattr(self.user, 'company') and self.user.company:
            location_qs = location_qs.filter(company=self.user.company)

        self.fields['location'].queryset = location_qs.order_by('name')

        selected_location_id = ''
        if self.is_bound:
            selected_location_id = (self.data.get('location') or '').strip()
        elif self.initial.get('location'):
            initial_location = self.initial.get('location')
            selected_location_id = str(getattr(initial_location, 'pk', initial_location))

        selected_location = None
        if selected_location_id:
            selected_location = self.fields['location'].queryset.filter(pk=selected_location_id).first()

        self._set_slot_choices(selected_location)

    def _parse_asset_ids(self, raw_ids):
        if not raw_ids:
            return []
        return [value.strip() for value in raw_ids.split(',') if value.strip()]

    def clean(self):
        cleaned_data = super().clean()
        clear_fields = []

        asset_ids = self._parse_asset_ids(cleaned_data.get('asset_ids'))
        if not asset_ids:
            raise ValidationError(_('Please select at least one asset.'))

        apply_quantity = cleaned_data.get('apply_quantity')
        if apply_quantity and apply_quantity > len(asset_ids):
            self.add_error('apply_quantity', _('Apply quantity cannot exceed selected assets.'))

        category = cleaned_data.get('category')
        brand = cleaned_data.get('brand')
        model = cleaned_data.get('model')

        if model:
            if brand and model.brand_id != brand.id:
                self.add_error('model', _('Selected model does not belong to selected brand.'))
            if category and model.category_id and model.category_id != category.id:
                self.add_error('model', _('Selected model does not belong to selected category.'))

        location = cleaned_data.get('location')
        zone = (cleaned_data.get('location_zone') or '').strip()
        rack = (cleaned_data.get('location_rack') or '').strip()
        shelf = (cleaned_data.get('location_shelf') or '').strip()
        slot_requested = bool(zone or rack or shelf)

        if slot_requested and not location:
            self.add_error('location', _('Please select a location when setting zone/rack/shelf.'))

        if location:
            if location.location_type != Location.LocationType.WAREHOUSE:
                cleaned_data['location_zone'] = None
                cleaned_data['location_rack'] = None
                cleaned_data['location_shelf'] = None
                clear_fields.extend(['location_zone', 'location_rack', 'location_shelf'])
            else:
                zones = set(location.expanded_zones())
                racks = set(location.expanded_racks())
                shelves = set(location.expanded_shelves())

                if not zones or not racks or not shelves:
                    raise ValidationError(_('The selected warehouse does not have valid zone/rack/shelf ranges configured.'))

                if not zone or zone not in zones:
                    self.add_error('location_zone', _('Please enter a valid zone for the selected warehouse.'))
                if not rack or rack not in racks:
                    self.add_error('location_rack', _('Please enter a valid rack for the selected warehouse.'))
                if not shelf or shelf not in shelves:
                    self.add_error('location_shelf', _('Please enter a valid shelf for the selected warehouse.'))

                cleaned_data['location_zone'] = zone
                cleaned_data['location_rack'] = rack
                cleaned_data['location_shelf'] = shelf

        update_data = self.get_update_data(cleaned_data)
        if not update_data:
            raise ValidationError(_('Please provide at least one field to update.'))

        cleaned_data['_clear_fields'] = clear_fields
        cleaned_data['asset_ids'] = asset_ids
        return cleaned_data

    def get_update_data(self, cleaned_data=None):
        data = cleaned_data or self.cleaned_data
        update_data = {}
        clear_fields = set(data.get('_clear_fields') or [])
        for field in self.editable_fields:
            value = data.get(field)
            if value is None:
                if field in clear_fields:
                    update_data[field] = None
                continue
            if isinstance(value, str) and value.strip() == '':
                continue
            update_data[field] = value
        return update_data
    
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
                status=CompanyUser.UserStatus.ACTIVE,
                user__isnull=False,
            ).select_related('user')

            self.fields['assigned_to'].queryset = User.objects.filter(
                id__in=[cu.user_id for cu in company_users]
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
    
    scheduled_date = forms.DateField(
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
    
    estimated_cost = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': _('0.00')
        })
    )
    
    assigned_to = forms.CharField(
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


class AssetImportForm(forms.Form):
    """
    Form for importing assets from CSV or Excel files.
    Supports bulk asset creation with validation and error reporting.
    """
    
    # File upload field
    file = forms.FileField(
        label=_('Import File'),
        help_text=_('Upload CSV or Excel file (.csv, .xlsx). Required columns: category, brand.'),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    # Company assignment for all imported assets
    company = forms.ModelChoiceField(
        queryset=Company.objects.all(),
        label=_('Default Company'),
        help_text=_('Company to assign all imported assets to (can be overridden in file)'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Asset number generation mode
    ASSET_NUMBER_CHOICES = [
        ('auto', _('Auto-generate asset numbers')),
        ('from_file', _('Use asset numbers from file')),
        ('prefix', _('Add prefix to existing numbers')),
    ]
    
    asset_number_mode = forms.ChoiceField(
        choices=ASSET_NUMBER_CHOICES,
        initial='auto',
        label=_('Asset Number Generation'),
        widget=forms.RadioSelect()
    )
    
    # Prefix for asset numbers (when using prefix mode)
    asset_number_prefix = forms.CharField(
        max_length=10,
        required=False,
        label=_('Asset Number Prefix'),
        help_text=_('Prefix to add to asset numbers (e.g., "ACME-")'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('ACME-')
        })
    )
    
    # Options for handling duplicate assets
    DUPLICATE_CHOICES = [
        ('skip', _('Skip duplicates (recommended)')),
        ('update', _('Update existing assets')),
        ('create_new', _('Create new assets with different numbers')),
    ]
    
    duplicate_handling = forms.ChoiceField(
        choices=DUPLICATE_CHOICES,
        initial='skip',
        label=_('Duplicate Handling'),
        help_text=_('How to handle assets that already exist (based on serial number)'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Validation options
    validate_only = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Validation Only'),
        help_text=_('Check this to validate the file without importing (preview mode)'),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        """Initialize form with user-specific company filtering."""
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter companies based on user access
        if self.user and not self.user.is_superuser:
            accessible_companies = self.user.get_accessible_companies()
            self.fields['company'].queryset = accessible_companies
        
        # Set default company if user has only one accessible company
        if self.user and hasattr(self.user, 'company') and self.user.company:
            self.fields['company'].initial = self.user.company
    
    def clean_file(self):
        """Validate uploaded file format and size."""
        file = self.cleaned_data.get('file')
        if not file:
            return file
        
        # Check file size (limit to 10MB)
        if file.size > 10 * 1024 * 1024:
            raise ValidationError(_('File size must be less than 10MB'))
        
        # Check file extension
        file_extension = file.name.lower().split('.')[-1]
        allowed_extensions = ['csv', 'xlsx', 'xls']
        
        if file_extension not in allowed_extensions:
            raise ValidationError(
                _('Invalid file format. Please upload CSV (.csv) or Excel (.xlsx, .xls) files only.')
            )
        
        return file
    
    def clean(self):
        """Additional form validation."""
        cleaned_data = super().clean()
        asset_number_mode = cleaned_data.get('asset_number_mode')
        asset_number_prefix = cleaned_data.get('asset_number_prefix')
        
        # Validate prefix is provided when prefix mode is selected
        if asset_number_mode == 'prefix' and not asset_number_prefix:
            raise ValidationError({
                'asset_number_prefix': _('Prefix is required when using prefix mode')
            })
        
        return cleaned_data


class AssetExportForm(forms.Form):
    """Form for asset export with filters and file format selection."""
    
    EXPORT_FORMAT_CHOICES = [
        ('csv', _('CSV (Comma Separated Values)')),
        ('excel', _('Excel Workbook (.xlsx)')),
        ('pdf', _('PDF Report')),
    ]
    
    # File format selection
    export_format = forms.ChoiceField(
        choices=EXPORT_FORMAT_CHOICES,
        initial='csv',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label=_('Export Format')
    )
    
    # Filter options
    status = forms.MultipleChoiceField(
        choices=[],  # Will be populated in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Status Filter')
    )
    
    category = forms.ModelMultipleChoiceField(
        queryset=AssetCategory.objects.none(),  # Will be populated in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Category Filter')
    )
    
    brand = forms.ModelMultipleChoiceField(
        queryset=AssetBrand.objects.none(),  # Will be populated in __init__
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Brand Filter')
    )
    
    # Date range filters
    created_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Created Date From')
    )
    
    created_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Created Date To')
    )
    
    purchase_date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Purchase Date From')
    )
    
    purchase_date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('Purchase Date To')
    )
    
    # Field selection
    include_fields = forms.MultipleChoiceField(
        choices=[
            ('asset_number', _('Asset Number')),
            ('category', _('Category')),
            ('brand', _('Brand')),
            ('model', _('Model')),
            ('serial_number', _('Serial Number')),
            ('description', _('Description')),
            ('status', _('Status')),
            ('location', _('Location')),
            ('assigned_to', _('Assigned To')),
            ('purchase_date', _('Purchase Date')),
            ('purchase_price', _('Purchase Price')),
            ('warranty_end_date', _('Warranty End Date')),
            ('created_at', _('Created At')),
            ('updated_at', _('Updated At')),
        ],
        initial=[
            'asset_number', 'category', 'brand', 'model', 'serial_number',
            'status', 'location', 'assigned_to', 'purchase_date'
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label=_('Fields to Include')
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate status choices from Asset model
        from .models import Asset
        self.fields['status'].choices = Asset.AssetStatus.choices
        
        if user and user.company:
            # Filter categories and brands by user's company
            self.fields['category'].queryset = hardware_category_queryset().order_by('name')
            
            self.fields['brand'].queryset = hardware_brand_queryset().order_by('name')
        else:
            self.fields['category'].queryset = hardware_category_queryset().order_by('name')
            self.fields['brand'].queryset = hardware_brand_queryset().order_by('name')
    
    def get_filtered_queryset(self, base_queryset):
        """Apply filters to the queryset based on form data."""
        cleaned_data = self.cleaned_data
        
        # Status filter
        if cleaned_data.get('status'):
            base_queryset = base_queryset.filter(status__in=cleaned_data['status'])
        
        # Category filter
        if cleaned_data.get('category'):
            base_queryset = base_queryset.filter(category__in=cleaned_data['category'])
        
        # Brand filter
        if cleaned_data.get('brand'):
            base_queryset = base_queryset.filter(brand__in=cleaned_data['brand'])
        
        # Date range filters
        if cleaned_data.get('created_date_from'):
            base_queryset = base_queryset.filter(created_at__date__gte=cleaned_data['created_date_from'])
        
        if cleaned_data.get('created_date_to'):
            base_queryset = base_queryset.filter(created_at__date__lte=cleaned_data['created_date_to'])
        
        if cleaned_data.get('purchase_date_from'):
            base_queryset = base_queryset.filter(purchase_date__gte=cleaned_data['purchase_date_from'])
        
        if cleaned_data.get('purchase_date_to'):
            base_queryset = base_queryset.filter(purchase_date__lte=cleaned_data['purchase_date_to'])
        
        return base_queryset


class BrandForm(forms.ModelForm):
    """Form for creating and editing asset brands."""
    
    class Meta:
        model = AssetBrand
        fields = ['name', 'code', 'description', 'website', 'support_email', 'support_phone', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter brand name')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter brand code (e.g., DELL, HP)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Enter brand description (optional)')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter website URL (optional)')
            }),
            'support_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter support email (optional)')
            }),
            'support_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter support phone (optional)')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class CategoryForm(forms.ModelForm):
    """Form for creating and editing asset categories."""
    
    class Meta:
        model = AssetCategory
        fields = ['name', 'code', 'description', 'parent', 'default_asset_model', 'depreciation_rate', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter category name')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter category code (e.g., LAPTOP, PHONE)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Enter category description (optional)')
            }),
            'parent': forms.Select(attrs={
                'class': 'form-select'
            }),
            'default_asset_model': forms.Select(attrs={
                'class': 'form-select'
            }),
            'depreciation_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'placeholder': _('Enter depreciation rate (0-100%)')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].queryset = hardware_category_queryset().order_by('name')
        self.fields['default_asset_model'].required = False
        self.fields['default_asset_model'].queryset = hardware_model_queryset().select_related('brand', 'category').order_by('category__name', 'brand__name', 'name')
        self.fields['default_asset_model'].empty_label = _('No default model')

    def clean(self):
        cleaned_data = super().clean()
        default_asset_model = cleaned_data.get('default_asset_model')
        if default_asset_model and not self.instance.pk:
            self.add_error('default_asset_model', _('Save the category first, then assign a default model.'))
        elif default_asset_model and default_asset_model.category_id and self.instance.pk and default_asset_model.category_id != self.instance.pk:
            self.add_error('default_asset_model', _('Default asset model must belong to this category.'))
        return cleaned_data


class ModelForm(forms.ModelForm):
    """Form for creating and editing asset models."""
    
    class Meta:
        model = AssetModel
        fields = ['category', 'brand', 'name', 'model_number', 'unit', 'description', 'specifications', 'is_active']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select'
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter model name')
            }),
            'model_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter official model number (optional)')
            }),
            'unit': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter default unit (e.g., PCS)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Enter model description (optional)')
            }),
            'specifications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': _('Enter technical specifications as JSON (optional)')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['category'].queryset = hardware_category_queryset().order_by('name')
        self.fields['category'].empty_label = _('Select category')
        self.fields['brand'].queryset = hardware_brand_queryset().order_by('name')
        self.fields['brand'].empty_label = _('Select brand')
        self.fields['model_number'].required = False
