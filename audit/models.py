"""
Audit models for HengJi Asset Management System.
This module provides comprehensive audit trail functionality for tracking
all changes and activities related to assets, users, and system operations.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
import uuid


class AuditLog(models.Model):
    """
    Central audit log for tracking all system activities.
    This model provides a comprehensive audit trail for compliance,
    security monitoring, and change tracking.
    """
    # Action types for different operations
    class ActionType(models.TextChoices):
        CREATE = 'create', _('Create')
        UPDATE = 'update', _('Update')
        DELETE = 'delete', _('Delete')
        LOGIN = 'login', _('Login')
        LOGOUT = 'logout', _('Logout')
        LOGIN_FAILED = 'login_failed', _('Failed Login')
        ASSIGN = 'assign', _('Assign Asset')
        RETURN = 'return', _('Return Asset')
        AUDIT = 'audit', _('Asset Audit')
        EXPORT = 'export', _('Data Export')
        IMPORT = 'import', _('Data Import')
        ACCESS = 'access', _('Access Resource')
        PERMISSION_CHANGE = 'permission_change', _('Permission Change')
        PASSWORD_CHANGE = 'password_change', _('Password Change')
        SETTINGS_CHANGE = 'settings_change', _('Settings Change')

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Who performed the action
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('User'),
        help_text=_('User who performed the action (null for system actions)')
    )

    # What action was performed
    action = models.CharField(
        max_length=20,
        choices=ActionType.choices,
        verbose_name=_('Action'),
        help_text=_('Type of action performed')
    )

    # What object was affected (using generic foreign key)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Content Type')
    )
    object_id = models.CharField(max_length=255, blank=True, verbose_name=_('Object ID'))
    content_object = GenericForeignKey('content_type', 'object_id')

    # Details about the action
    description = models.TextField(
        verbose_name=_('Description'),
        help_text=_('Human-readable description of what happened')
    )

    # Additional context data (JSON format)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional data about the action (before/after values, etc.)')
    )

    # Context information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address'),
        help_text=_('IP address from which the action was performed')
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent'),
        help_text=_('Browser/client user agent string')
    )

    # Timestamp
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp'),
        help_text=_('When the action occurred')
    )

    # Organization context
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name=_('Company'),
        help_text=_('Company context for the action')
    )

    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['company', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f"{user_str} - {self.get_action_display()} - {self.timestamp}"


class AssetAudit(models.Model):
    """
    Asset audit sessions for periodic verification of assets.
    Tracks scheduled and ad-hoc audits of assets including
    their physical verification and condition assessment.
    """
    # Audit status choices
    class AuditStatus(models.TextChoices):
        PLANNED = 'planned', _('Planned')
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    # Audit type choices
    class AuditType(models.TextChoices):
        SCHEDULED = 'scheduled', _('Scheduled Audit')
        SPOT_CHECK = 'spot_check', _('Spot Check')
        ANNUAL = 'annual', _('Annual Audit')
        INVENTORY = 'inventory', _('Full Inventory')
        COMPLIANCE = 'compliance', _('Compliance Audit')

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Audit identification
    audit_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Audit Number'),
        help_text=_('Unique identifier for this audit session')
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_('Audit Name'),
        help_text=_('Descriptive name for this audit')
    )

    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Purpose and scope of this audit')
    )

    # Audit configuration
    audit_type = models.CharField(
        max_length=20,
        choices=AuditType.choices,
        default=AuditType.SCHEDULED,
        verbose_name=_('Audit Type')
    )

    status = models.CharField(
        max_length=20,
        choices=AuditStatus.choices,
        default=AuditStatus.PLANNED,
        verbose_name=_('Status')
    )

    # Scope and organization
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='audits',
        verbose_name=_('Company')
    )

    divisions = models.ManyToManyField(
        'companies.Division',
        blank=True,
        related_name='audits',
        verbose_name=_('Divisions'),
        help_text=_('Specific divisions to audit (all if none selected)')
    )

    locations = models.ManyToManyField(
        'companies.Location',
        blank=True,
        related_name='audits',
        verbose_name=_('Locations'),
        help_text=_('Specific locations to audit (all if none selected)')
    )

    categories = models.ManyToManyField(
        'assets.AssetCategory',
        blank=True,
        related_name='audits',
        verbose_name=_('Categories'),
        help_text=_('Specific asset categories to audit (all if none selected)')
    )

    # Auditor assignment
    primary_auditor = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='primary_audits',
        verbose_name=_('Primary Auditor')
    )

    auditors = models.ManyToManyField(
        'accounts.User',
        related_name='audits',
        verbose_name=_('Auditors'),
        help_text=_('Users who can perform audits in this session')
    )

    # Scheduling
    planned_start_date = models.DateField(
        verbose_name=_('Planned Start Date')
    )

    planned_end_date = models.DateField(
        verbose_name=_('Planned End Date')
    )

    actual_start_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Actual Start Date')
    )

    actual_end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Actual End Date')
    )

    # Results summary
    total_assets_expected = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Assets Expected'),
        help_text=_('Expected number of assets to audit')
    )

    total_assets_found = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Assets Found'),
        help_text=_('Number of assets successfully located and verified')
    )

    total_assets_missing = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Assets Missing'),
        help_text=_('Number of assets that could not be located')
    )

    total_discrepancies = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Total Discrepancies'),
        help_text=_('Number of assets with information discrepancies')
    )

    # Notes and reporting
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('General notes about this audit')
    )

    report_generated = models.BooleanField(
        default=False,
        verbose_name=_('Report Generated'),
        help_text=_('Whether the audit report has been generated')
    )

    # Metadata
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_audits',
        verbose_name=_('Created By')
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Asset Audit')
        verbose_name_plural = _('Asset Audits')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.audit_number} - {self.name}"

    def get_completion_percentage(self):
        """Calculate audit completion percentage."""
        if self.total_assets_expected == 0:
            return 0
        audited = self.total_assets_found + self.total_assets_missing
        return (audited / self.total_assets_expected) * 100

    def is_overdue(self):
        """Check if audit is overdue."""
        from datetime import date
        if self.status in [self.AuditStatus.COMPLETED, self.AuditStatus.CANCELLED]:
            return False
        return date.today() > self.planned_end_date


class AssetAuditRecord(models.Model):
    """
    Individual asset verification records within an audit.
    Each record represents the verification of a single asset
    during an audit session.
    """
    # Verification status choices
    class VerificationStatus(models.TextChoices):
        FOUND = 'found', _('Found')
        MISSING = 'missing', _('Missing')
        DISCREPANCY = 'discrepancy', _('Discrepancy')
        DAMAGED = 'damaged', _('Damaged')
        UNAUTHORIZED = 'unauthorized', _('Unauthorized Asset')

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Related audit and asset
    audit = models.ForeignKey(
        AssetAudit,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name=_('Audit')
    )

    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='audit_records',
        verbose_name=_('Asset')
    )

    # Verification details
    status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        verbose_name=_('Verification Status')
    )

    # Physical verification
    physical_location_verified = models.BooleanField(
        default=False,
        verbose_name=_('Physical Location Verified'),
        help_text=_('Asset found in expected location')
    )

    actual_location = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('Actual Location'),
        help_text=_('Where the asset was actually found (if different)')
    )

    # Condition assessment
    condition_at_audit = models.CharField(
        max_length=20,
        choices=[],  # Will be populated from Asset.AssetCondition
        blank=True,
        verbose_name=_('Condition at Audit')
    )

    condition_notes = models.TextField(
        blank=True,
        verbose_name=_('Condition Notes'),
        help_text=_('Detailed notes about asset condition')
    )

    # Asset information verification
    serial_number_verified = models.BooleanField(
        default=False,
        verbose_name=_('Serial Number Verified'),
        help_text=_('Serial number matches system records')
    )

    actual_serial_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Actual Serial Number'),
        help_text=_('Serial number found on asset (if different)')
    )

    # Photos taken during audit
    verification_photo = models.ImageField(
        upload_to='audit/photos/',
        blank=True,
        null=True,
        verbose_name=_('Verification Photo'),
        help_text=_('Photo taken during audit for verification')
    )

    serial_number_photo = models.ImageField(
        upload_to='audit/serial_numbers/',
        blank=True,
        null=True,
        verbose_name=_('Serial Number Photo'),
        help_text=_('Close-up photo of asset serial number')
    )

    # Auditor and timing
    audited_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='audit_records',
        verbose_name=_('Audited By')
    )

    audited_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Audited At')
    )

    # Notes and discrepancies
    notes = models.TextField(
        blank=True,
        verbose_name=_('Audit Notes'),
        help_text=_('Detailed notes about this asset verification')
    )

    discrepancies = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Discrepancies'),
        help_text=_('Detailed list of any discrepancies found')
    )

    # Follow-up actions
    requires_follow_up = models.BooleanField(
        default=False,
        verbose_name=_('Requires Follow-up'),
        help_text=_('Whether this record requires follow-up action')
    )

    follow_up_assigned_to = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_follow_ups',
        verbose_name=_('Follow-up Assigned To')
    )

    follow_up_completed = models.BooleanField(
        default=False,
        verbose_name=_('Follow-up Completed')
    )

    class Meta:
        verbose_name = _('Asset Audit Record')
        verbose_name_plural = _('Asset Audit Records')
        ordering = ['audited_at']
        unique_together = [['audit', 'asset']]

    def __str__(self):
        return f"{self.audit.audit_number} - {self.asset.asset_number} ({self.get_status_display()})"

    def has_discrepancies(self):
        """Check if this record has any discrepancies."""
        return (
            self.status == self.VerificationStatus.DISCREPANCY or
            not self.physical_location_verified or
            not self.serial_number_verified or
            bool(self.discrepancies)
        )


class ChangeLog(models.Model):
    """
    Detailed change tracking for specific model fields.
    This model provides granular tracking of field-level changes
    for important models like Asset, User, Company, etc.
    """
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Related audit log entry
    audit_log = models.ForeignKey(
        AuditLog,
        on_delete=models.CASCADE,
        related_name='change_logs',
        verbose_name=_('Audit Log')
    )

    # Field that was changed
    field_name = models.CharField(
        max_length=100,
        verbose_name=_('Field Name'),
        help_text=_('Name of the field that was changed')
    )

    # Old and new values
    old_value = models.TextField(
        blank=True,
        verbose_name=_('Old Value'),
        help_text=_('Previous value of the field')
    )

    new_value = models.TextField(
        blank=True,
        verbose_name=_('New Value'),
        help_text=_('New value of the field')
    )

    # Data type information
    field_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Field Type'),
        help_text=_('Data type of the field (for proper display)')
    )

    class Meta:
        verbose_name = _('Change Log')
        verbose_name_plural = _('Change Logs')
        ordering = ['field_name']

    def __str__(self):
        return f"{self.field_name}: {self.old_value} → {self.new_value}"


class SystemEvent(models.Model):
    """
    System-level events and monitoring.
    Tracks important system events like failed logins,
    performance issues, errors, etc.
    """
    # Event severity levels
    class SeverityLevel(models.TextChoices):
        DEBUG = 'debug', _('Debug')
        INFO = 'info', _('Info')
        WARNING = 'warning', _('Warning')
        ERROR = 'error', _('Error')
        CRITICAL = 'critical', _('Critical')

    # Event categories
    class EventCategory(models.TextChoices):
        SECURITY = 'security', _('Security')
        PERFORMANCE = 'performance', _('Performance')
        ERROR = 'error', _('Error')
        MAINTENANCE = 'maintenance', _('Maintenance')
        BACKUP = 'backup', _('Backup')
        INTEGRATION = 'integration', _('Integration')

    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Event details
    event_type = models.CharField(
        max_length=100,
        verbose_name=_('Event Type'),
        help_text=_('Type of system event')
    )

    category = models.CharField(
        max_length=20,
        choices=EventCategory.choices,
        verbose_name=_('Category')
    )

    severity = models.CharField(
        max_length=20,
        choices=SeverityLevel.choices,
        default=SeverityLevel.INFO,
        verbose_name=_('Severity Level')
    )

    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('Detailed message about the event')
    )

    # Context data
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Metadata'),
        help_text=_('Additional event data and context')
    )

    # User context (if applicable)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_events',
        verbose_name=_('User')
    )

    # Network context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )

    # Timing
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp')
    )

    # Resolution tracking
    resolved = models.BooleanField(
        default=False,
        verbose_name=_('Resolved'),
        help_text=_('Whether this event has been resolved')
    )

    resolved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_system_events',
        verbose_name=_('Resolved By')
    )

    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Resolved At')
    )

    resolution_notes = models.TextField(
        blank=True,
        verbose_name=_('Resolution Notes'),
        help_text=_('Notes about how the event was resolved')
    )

    class Meta:
        verbose_name = _('System Event')
        verbose_name_plural = _('System Events')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['severity', '-timestamp']),
            models.Index(fields=['category', '-timestamp']),
            models.Index(fields=['resolved', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.get_severity_display()}: {self.event_type} ({self.timestamp})"
