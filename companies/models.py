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
        verbose_name=_('Division Code'),
        help_text=_('Unique identifier code for the division within the company')
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
        related_name='managed_divisions',
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
    