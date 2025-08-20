"""
Models for HengJi Asset Management System - Accounts App.
This module defines the custom user model and related authentication models.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class User(AbstractUser):
    """
    Custom user model for HengJi AMS with additional fields.
    """
    
    # Administrator role choices
    class AdminRole(models.TextChoices):
        SUPERADMIN = 'superadmin', _('Superadmin')
        IT_ADMINISTRATOR = 'it_administrator', _('IT Administrator')
        VIEWER = 'viewer', _('Viewer')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Administrator role field
    admin_role = models.CharField(
        max_length=20,
        choices=AdminRole.choices,
        null=True,
        blank=True,
        verbose_name=_('Administrator Role'),
        help_text=_('Role for administrator access levels')
    )
    
    # Profile image
    profile_image = models.ImageField(
        upload_to='profiles/',
        null=True,
        blank=True,
        verbose_name=_('Profile Image')
    )
    
    # Additional user fields
    employee_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name=_('Employee ID'),
        help_text=_('Unique employee identification number')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number')
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Department')
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
        verbose_name=_('Manager')
    )
    
    # 2FA settings
    two_factor_enabled = models.BooleanField(
        default=False,
        verbose_name=_('Two-Factor Authentication Enabled')
    )
    backup_tokens = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('2FA Backup Tokens')
    )
    
    # Security settings
    must_change_password = models.BooleanField(
        default=False,
        verbose_name=_('Must Change Password'),
        help_text=_('User must change password on next login')
    )
    
    # Profile settings
    language_preference = models.CharField(
        max_length=10,
        default='en',
        choices=[
            ('en', _('English')),
            ('zh-hans', _('Chinese (Simplified)')),
            ('zh-hant', _('Chinese (Traditional)')),
        ],
        verbose_name=_('Language Preference')
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        verbose_name=_('Timezone')
    )
    
    # Company association
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('Company')
    )
    division = models.ForeignKey(
        'companies.Division',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees',
        verbose_name=_('Division')
    )
    
    # Administrator access control
    # For IT Administrator role: company and/or division access
    managed_company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='it_administrators',
        verbose_name=_('Managed Company'),
        help_text=_('Company this IT administrator has access to')
    )
    
    # For IT Administrator role: division-specific access
    managed_divisions = models.ManyToManyField(
        'companies.Division',
        blank=True,
        related_name='it_administrators',
        verbose_name=_('Managed Divisions'),
        help_text=_('Divisions this IT administrator has access to')
    )
    
    # For Viewer role: location-specific access
    managed_locations = models.ManyToManyField(
        'companies.Location',
        blank=True,
        related_name='viewers',
        verbose_name=_('Managed Locations'),
        help_text=_('Locations this viewer has read-only access to')
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})" if self.get_full_name() else self.username
    
    def get_display_name(self):
        """Get the user's display name (full name or username)."""
        return self.get_full_name() or self.username
    
    def get_full_name_display(self):
        """Get the user's display name for navigation."""
        full_name = self.get_full_name()
        if full_name:
            return full_name
        return self.username
    
    # Permission methods for the new admin role system
    def is_superadmin(self):
        """Check if user is a superadmin with access to all data."""
        return (self.is_superuser or 
                self.admin_role == self.AdminRole.SUPERADMIN)
    
    def is_it_administrator(self):
        """Check if user is an IT administrator with division/company access."""
        return self.admin_role == self.AdminRole.IT_ADMINISTRATOR
    
    def is_viewer_admin(self):
        """Check if user is a viewer with location read-only access."""
        return self.admin_role == self.AdminRole.VIEWER
    
    def get_accessible_companies(self):
        """Get companies this admin can access."""
        if self.is_superadmin():
            from companies.models import Company
            return Company.objects.all()
        elif self.is_it_administrator():
            # IT Administrator can access companies through managed_company or managed_divisions
            companies = set()
            if self.managed_company:
                companies.add(self.managed_company)
            for division in self.managed_divisions.all():
                companies.add(division.company)
            return list(companies)
        elif self.is_viewer_admin():
            companies = set()
            for location in self.managed_locations.all():
                companies.add(location.company)
            return list(companies)
        return []
    
    def get_accessible_divisions(self):
        """Get divisions this admin can access."""
        if self.is_superadmin():
            from companies.models import Division
            return Division.objects.all()
        elif self.is_it_administrator():
            # IT Administrator can access divisions through managed_company or managed_divisions
            from companies.models import Division
            divisions = Division.objects.none()
            if self.managed_company:
                divisions = divisions | self.managed_company.divisions.all()
            divisions = divisions | self.managed_divisions.all()
            return divisions.distinct()
        elif self.is_viewer_admin():
            divisions = set()
            for location in self.managed_locations.all():
                if location.division:
                    divisions.add(location.division)
            return list(divisions)
        return []
    
    def get_accessible_locations(self):
        """Get locations this admin can access."""
        if self.is_superadmin():
            from companies.models import Location
            return Location.objects.all()
        elif self.is_it_administrator():
            # IT Administrator can access locations through managed_company or managed_divisions
            from companies.models import Location
            locations = Location.objects.none()
            if self.managed_company:
                locations = locations | self.managed_company.locations.all()
            for division in self.managed_divisions.all():
                locations = locations | division.locations.all()
            return locations.distinct()
        elif self.is_viewer_admin():
            return self.managed_locations.all()
        return []
    
    def get_accessible_assets(self):
        """Get assets this admin can access."""
        if self.is_superadmin():
            from assets.models import Asset
            return Asset.objects.all()
        elif self.is_it_administrator():
            # IT Administrator can access assets through managed_company or managed_divisions
            from assets.models import Asset
            assets = Asset.objects.none()
            if self.managed_company:
                assets = assets | Asset.objects.filter(company=self.managed_company)
            for division in self.managed_divisions.all():
                assets = assets | Asset.objects.filter(division=division)
            return assets.distinct()
        elif self.is_viewer_admin():
            from assets.models import Asset
            assets = Asset.objects.none()
            for location in self.managed_locations.all():
                assets = assets | Asset.objects.filter(location=location)
            return assets
        return []
    
    def can_manage_assets(self):
        """Check if user can manage assets."""
        return (self.is_superadmin() or 
                self.is_it_administrator() or
                self.has_perm('assets.add_asset'))
    
    def can_view_assets(self):
        """Check if user can view assets (including read-only)."""
        return (self.is_superadmin() or 
                self.is_it_administrator() or
                self.is_viewer_admin() or
                self.has_perm('assets.view_asset'))
    
    def can_edit_assets(self):
        """Check if user can edit assets (excludes viewers)."""
        return (self.is_superadmin() or 
                self.is_it_administrator())
    
    def can_manage_companies(self):
        """Check if user can manage companies."""
        return (self.is_superadmin() or
                self.has_perm('companies.add_company'))
    
    def can_view_audit(self):
        """Check if user can view audit logs."""
        return (self.is_superadmin() or 
                self.is_it_administrator() or
                self.has_perm('audit.view_auditlog'))
    
    def can_create_audit(self):
        """Check if user can create asset audits."""
        return (self.is_superadmin() or 
                self.is_it_administrator() or
                self.has_perm('audit.add_assetaudit'))
    
    def can_edit_audit(self, audit=None):
        """Check if user can edit a specific audit."""
        if self.is_superadmin():
            return True
        if self.is_it_administrator():
            if audit and hasattr(audit, 'company'):
                # Check if user has access to the audit's company
                return audit.company in self.get_accessible_companies()
            return True
        return self.has_perm('audit.change_assetaudit')
    
    def can_view_audit(self, audit=None):
        """Check if user can view a specific audit or audit logs."""
        if self.is_superadmin():
            return True
        if self.is_it_administrator():
            if audit and hasattr(audit, 'company'):
                # Check if user has access to the audit's company
                return audit.company in self.get_accessible_companies()
            return True
        return self.has_perm('audit.view_assetaudit') or self.has_perm('audit.view_auditlog')
    
    def can_view_reports(self):
        """Check if user can view reports."""
        return (self.is_superadmin() or 
                self.is_it_administrator() or
                self.is_viewer_admin() or
                self.has_perm('reports.view_report'))
    
    def can_manage_users(self):
        """Check if user can manage other users (only superadmins)."""
        return (self.is_superadmin() or
                self.has_perm('accounts.add_user'))
    
    def can_manage_company_users(self):
        """Check if user can manage company users."""
        return self.is_superadmin()
    
    def get_role_display_name(self):
        """Get the display name for the user's admin role."""
        if self.admin_role:
            return self.get_admin_role_display()
        else:
            return self.get_role_display()
    
    def get_access_scope_display(self):
        """Get a description of the user's access scope."""
        if self.is_superadmin():
            return _("All companies and data")
        elif self.is_it_administrator():
            # Show scope based on managed_company and/or managed_divisions
            scopes = []
            if self.managed_company:
                scopes.append(_("Company: {company}").format(company=self.managed_company.name))
            divisions = self.managed_divisions.all()
            if divisions.count() == 1:
                scopes.append(_("Division: {division}").format(division=divisions.first().name))
            elif divisions.count() > 1:
                scopes.append(_("{count} divisions").format(count=divisions.count()))
            return ", ".join(scopes) if scopes else _("No access configured")
        elif self.is_viewer_admin():
            locations = self.managed_locations.all()
            if locations.count() == 1:
                return _("Location: {location}").format(location=locations.first().name)
            else:
                return _("{count} locations").format(count=locations.count())
        return _("No admin access")
    
    # Legacy permission methods (for backward compatibility)
    def can_manage_assets_legacy(self):
        """Legacy method for asset management permissions."""
        return (self.role in ['admin', 'manager'] or 
                self.is_superuser or 
                self.has_perm('assets.add_asset'))
    
    def can_manage_companies_legacy(self):
        """Legacy method for company management permissions."""
        return (self.role == 'admin' or 
                self.is_superuser or
                self.has_perm('companies.add_company'))
    
    def can_view_audit_legacy(self):
        """Legacy method for audit view permissions."""
        return (self.role in ['admin', 'manager'] or 
                self.is_superuser or
                self.has_perm('audit.view_auditlog'))
    
    def can_view_reports_legacy(self):
        """Legacy method for reports view permissions."""
        return (self.role in ['admin', 'manager'] or 
                self.is_superuser or
                self.has_perm('reports.view_report'))
    
    def can_manage_users_legacy(self):
        """Legacy method for user management permissions."""
        return (self.role == 'admin' or 
                self.is_superuser or
                self.has_perm('accounts.add_user'))


class UserSession(models.Model):
    """
    Track user sessions for security and audit purposes.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions_history',
        verbose_name=_('User')
    )
    session_key = models.CharField(
        max_length=40,
        unique=True,
        verbose_name=_('Session Key')
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP Address')
    )
    user_agent = models.TextField(
        verbose_name=_('User Agent')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Activity')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"


class LoginAttempt(models.Model):
    """
    Track login attempts for security monitoring.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150,
        verbose_name=_('Username')
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_('IP Address')
    )
    user_agent = models.TextField(
        verbose_name=_('User Agent')
    )
    success = models.BooleanField(
        default=False,
        verbose_name=_('Successful')
    )
    failure_reason = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Failure Reason')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )
    
    class Meta:
        verbose_name = _('Login Attempt')
        verbose_name_plural = _('Login Attempts')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['username', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
        ]
    
    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.username} - {status} - {self.timestamp}"
