"""
Models for HengJi Asset Management System - Accounts App.
This module defines the custom user model and related authentication models.
"""

import base64
import hashlib
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class AdminRole(models.Model):
    """Persistent administrator roles that can be assigned additively to users."""

    code = models.CharField(max_length=64, unique=True, verbose_name=_('Role Code'))
    name = models.CharField(max_length=120, verbose_name=_('Role Name'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Administrator Role')
        verbose_name_plural = _('Administrator Roles')
        ordering = ['name']

    def __str__(self):
        return self.name


def _xor_secret(value):
    key = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    raw = value.encode('utf-8')
    protected = bytes(raw[index] ^ key[index % len(key)] for index in range(len(raw)))
    return base64.urlsafe_b64encode(protected).decode('ascii')


def _xor_secret_restore(value):
    key = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    raw = base64.urlsafe_b64decode(value.encode('ascii'))
    restored = bytes(raw[index] ^ key[index % len(key)] for index in range(len(raw)))
    return restored.decode('utf-8')


class User(AbstractUser):
    """
    Custom user model for HengJi AMS with additional fields.
    """
    
    # Administrator role choices
    class AdminRole(models.TextChoices):
        SUPERADMIN = 'superadmin', _('Superadmin')
        IT_ADMINISTRATOR = 'it_administrator', _('IT Administrator')
        VIEWER = 'viewer', _('Viewer')
        ORDER_MANAGEMENT_PROCUREMENT_SPECIALIST = 'order_management_procurement_specialist', _('Order Management & Procurement Specialist')

    LANGUAGE_CHOICES = [
        ('en-us', _('English (US)')),
        ('zh-cn', _('Chinese (Simplified)')),
    ]

    LANGUAGE_CODE_ALIASES = {
        'en': 'en-us',
        'en-us': 'en-us',
        'zh-cn': 'zh-cn',
        'zh-hans': 'zh-cn',
        'zh-hant': 'zh-cn',
    }
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Administrator role assignments
    roles = models.ManyToManyField(
        'accounts.AdminRole',
        blank=True,
        related_name='users',
        verbose_name=_('Administrator Roles'),
        help_text=_('Roles for administrator access levels')
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
    force_2fa_setup = models.BooleanField(
        default=False,
        verbose_name=_('Force 2FA Setup'),
        help_text=_('User must set up 2FA on next login')
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
        default='en-us',
        choices=LANGUAGE_CHOICES,
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

    @classmethod
    def normalize_language_code(cls, language_code):
        """Normalize legacy language codes to currently supported settings."""
        if not language_code:
            return 'en-us'
        return cls.LANGUAGE_CODE_ALIASES.get(language_code.lower(), 'en-us')

    def save(self, *args, **kwargs):
        self.language_preference = self.normalize_language_code(self.language_preference)
        result = super().save(*args, **kwargs)
        pending_role_codes = getattr(self, '_pending_admin_role_codes', None)
        if pending_role_codes is not None:
            self.set_admin_roles(pending_role_codes)
            delattr(self, '_pending_admin_role_codes')
        return result

    @classmethod
    def order_admin_role_codes(cls, role_codes):
        ordered_codes = []
        input_codes = [code for code in role_codes if code]
        for code, _label in cls.AdminRole.choices:
            if code in input_codes and code not in ordered_codes:
                ordered_codes.append(code)
        for code in input_codes:
            if code not in ordered_codes:
                ordered_codes.append(code)
        return ordered_codes

    @classmethod
    def admin_role_label(cls, role_code):
        return str(dict(cls.AdminRole.choices).get(role_code, role_code or ''))

    @property
    def admin_role(self):
        role_codes = self.get_admin_role_codes()
        return role_codes[0] if role_codes else ''

    @admin_role.setter
    def admin_role(self, value):
        if isinstance(value, (list, tuple, set)):
            self._pending_admin_role_codes = self.order_admin_role_codes(value)
        elif value:
            self._pending_admin_role_codes = [value]
        else:
            self._pending_admin_role_codes = []

    def has_admin_role(self, role_code):
        pending_role_codes = getattr(self, '_pending_admin_role_codes', None)
        if pending_role_codes is not None:
            return role_code in pending_role_codes
        if not self.pk:
            return False
        return self.roles.filter(code=role_code).exists()

    def get_admin_role_codes(self):
        pending_role_codes = getattr(self, '_pending_admin_role_codes', None)
        if pending_role_codes is not None:
            return self.order_admin_role_codes(pending_role_codes)
        if not self.pk:
            return []
        return self.order_admin_role_codes(self.roles.values_list('code', flat=True))

    def set_admin_roles(self, role_codes):
        normalized_codes = self.order_admin_role_codes(role_codes or [])
        if not self.pk:
            self._pending_admin_role_codes = normalized_codes
            return
        roles = AdminRole.objects.filter(code__in=normalized_codes)
        self.roles.set(roles)

    def get_admin_role_display(self):
        return self.admin_role_label(self.admin_role)

    def get_admin_roles_display(self):
        role_codes = self.get_admin_role_codes()
        if not role_codes:
            return _('No admin roles')
        return ', '.join(self.admin_role_label(code) for code in role_codes)
    
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
                self.has_admin_role(self.AdminRole.SUPERADMIN))
    
    def is_it_administrator(self):
        """Check if user is an IT administrator with division/company access."""
        return self.has_admin_role(self.AdminRole.IT_ADMINISTRATOR)
    
    def is_viewer_admin(self):
        """Check if user is a viewer with location read-only access."""
        return self.has_admin_role(self.AdminRole.VIEWER)

    def is_order_management_procurement_specialist(self):
        """Check if user can handle order-management and procurement workflows."""
        return self.has_admin_role(self.AdminRole.ORDER_MANAGEMENT_PROCUREMENT_SPECIALIST)
    
    def get_accessible_companies(self):
        """Get companies this admin can access."""
        from companies.models import Company

        if self.is_superadmin():
            return Company.objects.all()

        company_ids = set()
        if self.managed_company_id and self.is_it_administrator():
            company_ids.add(self.managed_company_id)
        if self.is_it_administrator():
            company_ids.update(self.managed_divisions.values_list('company_id', flat=True))
        if self.is_viewer_admin():
            company_ids.update(self.managed_locations.values_list('company_id', flat=True))
        return Company.objects.filter(id__in=company_ids)
    
    def get_accessible_divisions(self):
        """Get divisions this admin can access."""
        from companies.models import Division

        if self.is_superadmin():
            return Division.objects.all()

        division_ids = set()
        if self.managed_company_id and self.is_it_administrator():
            division_ids.update(self.managed_company.divisions.values_list('id', flat=True))
        if self.is_it_administrator():
            division_ids.update(self.managed_divisions.values_list('id', flat=True))
        if self.is_viewer_admin():
            division_ids.update(self.managed_locations.exclude(division__isnull=True).values_list('division_id', flat=True))
        return Division.objects.filter(id__in=division_ids)
    
    def get_accessible_locations(self):
        """Get locations this admin can access."""
        from companies.models import Location

        if self.is_superadmin():
            return Location.objects.all()

        location_ids = set()
        if self.managed_company_id and self.is_it_administrator():
            location_ids.update(self.managed_company.locations.values_list('id', flat=True))
        if self.is_it_administrator():
            location_ids.update(Location.objects.filter(division__in=self.managed_divisions.all()).values_list('id', flat=True))
        if self.is_viewer_admin():
            location_ids.update(self.managed_locations.values_list('id', flat=True))
        return Location.objects.filter(id__in=location_ids)
    
    def get_accessible_assets(self):
        """Get assets this admin can access."""
        from assets.models import Asset

        if self.is_superadmin():
            return Asset.objects.all()

        asset_queryset = Asset.objects.none()
        if self.managed_company_id and self.is_it_administrator():
            asset_queryset = asset_queryset | Asset.objects.filter(company=self.managed_company)
        if self.is_it_administrator():
            asset_queryset = asset_queryset | Asset.objects.filter(division__in=self.managed_divisions.all())
        if self.is_viewer_admin():
            asset_queryset = asset_queryset | Asset.objects.filter(location__in=self.managed_locations.all())
        return asset_queryset.distinct()
    
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

    def can_manage_orders(self):
        """Check if user can access order-management workflows."""
        return self.is_superadmin() or self.is_order_management_procurement_specialist()
    
    def get_role_display_name(self):
        """Get the display name for the user's admin role."""
        if self.get_admin_role_codes():
            return self.get_admin_roles_display()
        if hasattr(self, 'get_role_display') and getattr(self, 'role', None):
            return self.get_role_display()
        return _('Standard User')
    
    def get_access_scope_display(self):
        """Get a description of the user's access scope."""
        if self.is_superadmin():
            return _("All companies and data")

        scopes = []
        if self.is_it_administrator():
            if self.managed_company:
                scopes.append(_("Company: {company}").format(company=self.managed_company.name))
            divisions = self.managed_divisions.all()
            if divisions.count() == 1:
                scopes.append(_("Division: {division}").format(division=divisions.first().name))
            elif divisions.count() > 1:
                scopes.append(_("{count} divisions").format(count=divisions.count()))
        if self.is_viewer_admin():
            locations = self.managed_locations.all()
            if locations.count() == 1:
                scopes.append(_("Location: {location}").format(location=locations.first().name))
            elif locations.count() > 1:
                scopes.append(_("{count} locations").format(count=locations.count()))
        if self.is_order_management_procurement_specialist():
            scopes.append(_("Order management and procurement workflows"))
        return ", ".join(scopes) if scopes else _("No admin access")


class UserMailboxSettings(models.Model):
    """Per-user mailbox configuration for order-management workflows."""

    class ReceiveProtocol(models.TextChoices):
        IMAP = 'imap', _('IMAP')
        POP3 = 'pop3', _('POP3')

    class ConnectionSecurity(models.TextChoices):
        NONE = 'none', _('None')
        SSL_TLS = 'ssl_tls', _('SSL/TLS')
        STARTTLS = 'starttls', _('STARTTLS')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mailbox_settings',
        verbose_name=_('User'),
    )
    email_address = models.EmailField(verbose_name=_('Email Address'))
    display_name = models.CharField(max_length=150, blank=True, verbose_name=_('Display Name'))
    username = models.CharField(max_length=255, verbose_name=_('Login Username'))
    encrypted_password = models.TextField(blank=True, verbose_name=_('Encrypted Password'))
    receive_protocol = models.CharField(
        max_length=10,
        choices=ReceiveProtocol.choices,
        default=ReceiveProtocol.IMAP,
        verbose_name=_('Receive Protocol'),
    )
    imap_host = models.CharField(max_length=255, blank=True, verbose_name=_('IMAP Host'))
    imap_port = models.PositiveIntegerField(default=993, verbose_name=_('IMAP Port'))
    imap_security = models.CharField(
        max_length=10,
        choices=ConnectionSecurity.choices,
        default=ConnectionSecurity.SSL_TLS,
        verbose_name=_('IMAP Security'),
    )
    pop3_host = models.CharField(max_length=255, blank=True, verbose_name=_('POP3 Host'))
    pop3_port = models.PositiveIntegerField(default=995, verbose_name=_('POP3 Port'))
    pop3_security = models.CharField(
        max_length=10,
        choices=ConnectionSecurity.choices,
        default=ConnectionSecurity.SSL_TLS,
        verbose_name=_('POP3 Security'),
    )
    smtp_host = models.CharField(max_length=255, verbose_name=_('SMTP Host'))
    smtp_port = models.PositiveIntegerField(default=465, verbose_name=_('SMTP Port'))
    smtp_security = models.CharField(
        max_length=10,
        choices=ConnectionSecurity.choices,
        default=ConnectionSecurity.SSL_TLS,
        verbose_name=_('SMTP Security'),
    )
    sync_lookback_months = models.PositiveIntegerField(default=6, verbose_name=_('Sync Lookback Months'))
    imap_sent_folder = models.CharField(max_length=120, default='Sent', verbose_name=_('IMAP Sent Folder'))
    sync_outbox = models.BooleanField(default=True, verbose_name=_('Sync Outbox'))
    auto_sync_enabled = models.BooleanField(default=True, verbose_name=_('Auto Sync Enabled'))
    is_active = models.BooleanField(default=True, verbose_name=_('Active'))
    last_mailbox_sync_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Last Mailbox Sync At'))
    last_connection_test_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Last Connection Test At'))
    last_connection_status = models.CharField(max_length=40, blank=True, verbose_name=_('Last Connection Status'))
    last_connection_message = models.TextField(blank=True, verbose_name=_('Last Connection Message'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('User Mailbox Settings')
        verbose_name_plural = _('User Mailbox Settings')

    def __str__(self):
        return f'{self.user.username} mailbox'

    @property
    def password(self):
        if not self.encrypted_password:
            return ''
        try:
            return _xor_secret_restore(self.encrypted_password)
        except Exception:
            return ''

    def set_password(self, raw_password):
        self.encrypted_password = _xor_secret(raw_password) if raw_password else ''

    def save(self, *args, **kwargs):
        if self.email_address and not self.display_name:
            self.display_name = self.user.get_display_name()
        super().save(*args, **kwargs)


class ReceivedEmailMessage(models.Model):
    """Locally cached mailbox messages for the order-management email module."""

    class MessageDirection(models.TextChoices):
        INBOX = 'inbox', _('Inbox')
        OUTBOX = 'outbox', _('Outbox')

    mailbox = models.ForeignKey(
        UserMailboxSettings,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_('Mailbox'),
    )
    direction = models.CharField(
        max_length=10,
        choices=MessageDirection.choices,
        default=MessageDirection.INBOX,
        verbose_name=_('Direction'),
    )
    external_id = models.CharField(max_length=255, verbose_name=_('External ID'))
    message_id = models.CharField(max_length=255, blank=True, verbose_name=_('Message-ID'))
    folder_name = models.CharField(max_length=120, blank=True, verbose_name=_('Folder'))
    subject = models.CharField(max_length=255, blank=True, verbose_name=_('Subject'))
    sender = models.CharField(max_length=255, blank=True, verbose_name=_('Sender'))
    recipients = models.TextField(blank=True, verbose_name=_('Recipients'))
    received_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Received At'))
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Sent At'))
    body_preview = models.TextField(blank=True, verbose_name=_('Body Preview'))
    body_text = models.TextField(blank=True, verbose_name=_('Body Text'))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Metadata'))
    is_read = models.BooleanField(default=False, verbose_name=_('Read'))
    synced_at = models.DateTimeField(auto_now=True, verbose_name=_('Synced At'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        verbose_name = _('Received Email Message')
        verbose_name_plural = _('Received Email Messages')
        ordering = ['-received_at', '-sent_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['mailbox', 'direction', 'external_id'], name='uniq_mailbox_direction_external_message'),
        ]

    def __str__(self):
        return self.subject or self.external_id

    @property
    def event_at(self):
        return self.received_at or self.sent_at or self.created_at
    
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
