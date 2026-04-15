"""
Company and Division models for HengJi Asset Management System.
This module defines the organizational structure models that support
multi-company and multi-division asset management.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model


class Company(models.Model):
    """
    Company model representing different organizations using the system.
    Each company can have multiple divisions and manage their own assets.
    """
    
    # Company status choices
    class CompanyStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
    
    # Basic company information
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name=_('Company Name'),
        help_text=_('Official name of the company')
    )
    
    code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('Company Code'),
        help_text=_('Unique identifier code for the company (used in asset numbering)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Brief description of the company')
    )
    
    # Contact information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name=_('Phone Number')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email'),
        help_text=_('Company contact email')
    )
    
    website = models.URLField(
        blank=True,
        verbose_name=_('Website'),
        help_text=_('Company website URL')
    )
    
    # Address information
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Address Line 1')
    )
    
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Address Line 2')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('City')
    )
    
    state_province = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('State/Province')
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Postal Code')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Country')
    )
    
    # Company settings
    status = models.CharField(
        max_length=20,
        choices=CompanyStatus.choices,
        default=CompanyStatus.ACTIVE,
        verbose_name=_('Status'),
        help_text=_('Current status of the company')
    )
    
    logo = models.ImageField(
        upload_to='companies/logos/',
        blank=True,
        null=True,
        verbose_name=_('Company Logo'),
        help_text=_('Upload company logo (optional)')
    )
    
    # Asset numbering settings
    asset_prefix = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Asset Prefix'),
        help_text=_('Prefix used for asset numbering (e.g., "COMP-")')
    )
    
    next_asset_number = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Next Asset Number'),
        help_text=_('Next number to be used for asset numbering')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        """Return the full formatted address."""
        address_parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state_province,
            self.postal_code,
            self.country
        ]
        return ', '.join(filter(None, address_parts))
    
    def generate_next_asset_number(self):
        """Generate the next asset number for this company."""
        asset_number = f"{self.asset_prefix}{self.next_asset_number}"
        self.next_asset_number += 1
        self.save()
        return asset_number


class Division(models.Model):
    """
    Division model representing departments or divisions within a company.
    Each division can have its own asset management and user access controls.
    """
    
    # Division status choices
    class DivisionStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        MERGED = 'merged', _('Merged')
    
    # Basic division information
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='divisions',
        verbose_name=_('Company'),
        help_text=_('Company this division belongs to')
    )
    
    name = models.CharField(
        max_length=200,
        verbose_name=_('Division Name'),
        help_text=_('Name of the division or department')
    )
    
    code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Division Code'),
        help_text=_('Unique identifier code for the division within the company (optional)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Brief description of the division')
    )
    
    # Division hierarchy
    parent_division = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='subdivisions',
        verbose_name=_('Parent Division'),
        help_text=_('Parent division if this is a sub-division')
    )
    
    # Contact information
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='division_manager_for',
        verbose_name=_('Division Manager'),
        help_text=_('User responsible for managing this division')
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message=_("Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    )
    
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name=_('Phone Number')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email'),
        help_text=_('Division contact email')
    )
    
    # Location information
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Location'),
        help_text=_('Physical location of the division')
    )
    
    building = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Building'),
        help_text=_('Building name or number')
    )
    
    floor = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Floor'),
        help_text=_('Floor number or name')
    )
    
    room = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Room'),
        help_text=_('Room number or name')
    )
    
    # Division settings
    status = models.CharField(
        max_length=20,
        choices=DivisionStatus.choices,
        default=DivisionStatus.ACTIVE,
        verbose_name=_('Status'),
        help_text=_('Current status of the division')
    )
    
    # Budget and cost center
    budget_code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Budget Code'),
        help_text=_('Budget or cost center code for this division')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))


class Location(models.Model):
    """
    Location model representing physical locations within companies.
    Locations can be buildings, floors, rooms, or any physical space
    where assets can be placed.
    """
    
    class LocationType(models.TextChoices):
        BUILDING = 'building', _('Building')
        FLOOR = 'floor', _('Floor')
        ROOM = 'room', _('Room')
        WAREHOUSE = 'warehouse', _('Warehouse')
        OFFICE = 'office', _('Office')
        FACTORY = 'factory', _('Factory')
        OTHER = 'other', _('Other')
    
    class LocationStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        MAINTENANCE = 'maintenance', _('Under Maintenance')
    
    # Basic location information
    name = models.CharField(
        max_length=200,
        verbose_name=_('Location Name'),
        help_text=_('Name of the location')
    )
    
    code = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Location Code'),
        help_text=_('Unique code for the location (e.g., B1-F3-R101)')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Detailed description of the location')
    )
    
    # Hierarchy
    company = models.ForeignKey(
        'Company',
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('Company')
    )
    
    division = models.ForeignKey(
        'Division',
        on_delete=models.CASCADE,
        related_name='locations',
        blank=True,
        null=True,
        verbose_name=_('Division')
    )
    
    parent_location = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='child_locations',
        blank=True,
        null=True,
        verbose_name=_('Parent Location'),
        help_text=_('Parent location in hierarchy (e.g., floor for room)')
    )
    
    # Location details
    location_type = models.CharField(
        max_length=20,
        choices=LocationType.choices,
        default=LocationType.ROOM,
        verbose_name=_('Location Type')
    )
    
    status = models.CharField(
        max_length=20,
        choices=LocationStatus.choices,
        default=LocationStatus.ACTIVE,
        verbose_name=_('Status')
    )
    
    # Physical details
    area_size = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_('Area Size (sq meters)'),
        help_text=_('Size of the location in square meters')
    )
    
    capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name=_('Capacity'),
        help_text=_('Maximum capacity (people, assets, etc.)')
    )
    
    # Address information
    address_line1 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Address Line 1')
    )
    
    address_line2 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('Address Line 2')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('City')
    )
    
    state_province = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('State/Province')
    )
    
    postal_code = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Postal Code')
    )
    
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Country')
    )
    
    # Contact information
    manager = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='location_manager_for',
        blank=True,
        null=True,
        verbose_name=_('Location Manager')
    )
    
    phone_number = models.CharField(
        max_length=17,
        blank=True,
        verbose_name=_('Phone Number')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('Email')
    )
    
    # Coordinates for mapping
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Latitude'),
        help_text=_('GPS latitude coordinate')
    )
    
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        blank=True,
        null=True,
        verbose_name=_('Longitude'),
        help_text=_('GPS longitude coordinate')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('Location')
        verbose_name_plural = _('Locations')
        ordering = ['company', 'name']
        unique_together = [['company', 'code']]
    
    def __str__(self):
        return f"{self.company.name} - {self.name}"
    
    def get_full_path(self):
        """Return the full hierarchical path of the location."""
        path = [self.name]
        parent = self.parent_location
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent_location
        return " > ".join(path)
    
    def get_full_address(self):
        """Return formatted address string."""
        address_parts = []
        if self.address_line1:
            address_parts.append(self.address_line1)
        if self.address_line2:
            address_parts.append(self.address_line2)
        if self.city:
            address_parts.append(self.city)
        if self.state_province:
            address_parts.append(self.state_province)
        if self.postal_code:
            address_parts.append(self.postal_code)
        if self.country:
            address_parts.append(self.country)
        return ", ".join(address_parts)
    
    def get_children_count(self):
        """Return count of child locations."""
        return self.child_locations.count()
    
    def get_assets_count(self):
        """Return count of assets in this location."""
        from assets.models import Asset
        return Asset.objects.filter(location=self).count()


class CompanyUser(models.Model):
    """
    Junction model for associating users with companies and their roles.
    Allows users to belong to multiple companies with different roles.
    """
    
    # User role choices for company access
    class CompanyRole(models.TextChoices):
        EMPLOYEE = 'employee', _('Employee')
        MANAGER = 'manager', _('Manager')
        ADMIN = 'admin', _('Company Admin')
        VIEWER = 'viewer', _('Viewer')
    
    # User status within company
    class UserStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        INACTIVE = 'inactive', _('Inactive')
        SUSPENDED = 'suspended', _('Suspended')
    
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='company_memberships',
        verbose_name=_('User')
    )
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_users',
        verbose_name=_('Company')
    )
    
    role = models.CharField(
        max_length=20,
        choices=CompanyRole.choices,
        default=CompanyRole.EMPLOYEE,
        verbose_name=_('Role'),
        help_text=_('User role within the company')
    )
    
    division = models.ForeignKey(
        Division,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='division_users',
        verbose_name=_('Division'),
        help_text=_('Primary division for this user')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='location_users',
        verbose_name=_('Primary Location'),
        help_text=_('Primary work location for this user')
    )
    
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE,
        verbose_name=_('Status')
    )
    
    # Employee details
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Employee ID'),
        help_text=_('Company employee identification number')
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Department'),
        help_text=_('Department or team within the company')
    )
    
    job_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Job Title')
    )
    
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        verbose_name=_('Manager'),
        help_text=_('Direct manager for this user')
    )
    
    # Dates
    hire_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Hire Date')
    )
    
    start_date = models.DateField(
        auto_now_add=True,
        verbose_name=_('Company Start Date'),
        help_text=_('Date when user joined this company in the system')
    )
    
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('End Date'),
        help_text=_('Date when user left the company')
    )
    
    # Contact within company
    work_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Work Phone')
    )
    
    work_email = models.EmailField(
        blank=True,
        verbose_name=_('Work Email'),
        help_text=_('Company email address if different from user email')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Company User')
        verbose_name_plural = _('Company Users')
        unique_together = ['user', 'company']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['employee_id']),
        ]
        ordering = ['company__name', 'user__last_name', 'user__first_name']
    
    def __str__(self):
        return f"{self.user.get_full_name_display()} - {self.company.name} ({self.get_role_display()})"
    
    def can_manage_assets(self):
        """Check if user can manage assets for this company."""
        return self.role in [self.CompanyRole.ADMIN, self.CompanyRole.MANAGER]
    
    def can_view_company_data(self):
        """Check if user can view company data."""
        return self.status == self.UserStatus.ACTIVE
    
    def get_accessible_locations(self):
        """Return locations this user can access."""
        if self.role == self.CompanyRole.ADMIN:
            return self.company.locations.all()
        elif self.division:
            return self.division.locations.all()
        elif self.location:
            return Location.objects.filter(pk=self.location.pk)
        return Location.objects.none()
    
    def get_full_display_name(self):
        """Return full display name with company context."""
        title = f" ({self.job_title})" if self.job_title else ""
        return f"{self.user.get_full_name_display()}{title} - {self.company.name}"
