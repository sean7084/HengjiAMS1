"""Regression tests for two defects found by the ruff correctness gate.

Kept in a separate module (like ``api/tests_miniprogram.py``) because
``accounts/tests.py`` predates this work and uses tab indentation.

- Issue #69: ``setup_2fa_simple`` raised ``UnboundLocalError`` (F823).
- Issue #70: ``User.can_view_audit`` was defined twice (F811).
"""
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from audit.models import AssetAudit
from companies.models import Company

from .models import User


class Setup2FaSimpleRegressionTests(TestCase):
    """Issue #69 - the gettext alias was shadowed by a loop variable.

    ``setup_2fa_simple`` generated backup tokens with ``for _ in range(10)``.
    Assigning to ``_`` anywhere in a function makes it local for the *whole*
    function, so the earlier translation call
    ``_('Two-factor authentication is already enabled.')`` raised
    ``UnboundLocalError`` - a 500 for any user who already had 2FA enabled.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='eng2fa', password='pw')

    def test_already_enabled_redirects_instead_of_raising(self):
        self.user.two_factor_enabled = True
        self.user.save(update_fields=['two_factor_enabled'])
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:setup_2fa'))

        self.assertRedirects(response, reverse('accounts:profile'))

    def test_get_for_user_without_2fa_does_not_raise(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:setup_2fa'))
        # Whatever the page renders, it must not be a server error.
        self.assertNotEqual(response.status_code, 500)


class CanViewAuditCapabilityTests(TestCase):
    """Issue #70 - ``can_view_audit`` was defined twice.

    The first definition took no argument and checked only
    ``audit.view_auditlog``; the second (the one Python kept) takes an optional
    ``audit`` and also accepts ``audit.view_assetaudit``. Both call shapes are
    live in the codebase: the log-list views call ``can_view_audit()``, while the
    audit detail/edit views call ``can_view_audit(audit)`` for company scoping.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='auditor', password='pw')
        self.company = Company.objects.create(name='Kering', code='KER')

    def _make_audit(self):
        return AssetAudit.objects.create(
            audit_number='AUD-0001',
            name='Annual stocktake',
            company=self.company,
            primary_auditor=self.user,
            planned_start_date=timezone.localdate(),
            planned_end_date=timezone.localdate(),
        )

    def _with_permission(self, codename):
        self.user.user_permissions.add(Permission.objects.get(codename=codename))
        # Permission lookups are cached on the user instance.
        return User.objects.get(pk=self.user.pk)

    def test_no_argument_call_is_supported(self):
        self.assertIs(self.user.can_view_audit(), False)

    def test_object_level_call_is_supported(self):
        self.assertIs(self.user.can_view_audit(self._make_audit()), False)

    def test_view_auditlog_permission_grants_access(self):
        self.assertIs(self._with_permission('view_auditlog').can_view_audit(), True)

    def test_view_assetaudit_permission_grants_access(self):
        # The dead definition only checked view_auditlog, so this asserts that
        # the surviving (broader) definition is the one in effect.
        self.assertIs(self._with_permission('view_assetaudit').can_view_audit(), True)

    def test_superadmin_can_view_any_audit(self):
        self.user.is_superuser = True
        self.user.save(update_fields=['is_superuser'])
        self.assertIs(self.user.can_view_audit(self._make_audit()), True)

    def test_permission_holder_falls_through_without_company_scoping(self):
        other = Company.objects.create(name='Other Client', code='OTH')
        audit = AssetAudit.objects.create(
            audit_number='AUD-0002',
            name='Other stocktake',
            company=other,
            primary_auditor=self.user,
            planned_start_date=timezone.localdate(),
            planned_end_date=timezone.localdate(),
        )
        holder = self._with_permission('view_assetaudit')
        # Company scoping only applies to IT administrators; a plain permission
        # holder reaches the has_perm() fallback and is not scoped, so an audit
        # belonging to another company is still visible. Documenting that
        # behaviour here so a change to it is a conscious decision.
        self.assertIs(holder.can_view_audit(audit), True)
