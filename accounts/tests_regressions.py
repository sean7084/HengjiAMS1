"""Regression tests for a defect found by the ruff correctness gate.

Kept in a separate module (like ``api/tests_miniprogram.py``) because
``accounts/tests.py`` predates this work and uses tab indentation.

- Issue #69: ``setup_2fa_simple`` raised ``UnboundLocalError`` (F823).

(The former Issue #70 regression for ``User.can_view_audit`` was removed when the
audit app and its permission helpers were retired in favour of domain-specific
activity logs in ``assets`` and ``inspections``.)
"""
from django.test import TestCase
from django.urls import reverse

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
