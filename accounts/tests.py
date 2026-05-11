from django.test import TestCase
from django.urls import reverse

from .models import AdminRole, User


class UserEditViewTests(TestCase):
	@classmethod
	def setUpTestData(cls):
		cls.admin_user = User.objects.create_superuser(
			username='admin_user',
			email='admin@example.com',
			password='AdminPass123!'
		)
		cls.viewer_role = AdminRole.objects.get(code=User.AdminRole.VIEWER)
		cls.order_management_manager_role = AdminRole.objects.get(code=User.AdminRole.ORDER_MANAGEMENT_MANAGER)

		cls.target_user = User.objects.create_user(
			username='target_user',
			email='target@example.com',
			password='TargetPass123!',
			first_name='Target',
			last_name='User',
			language_preference='en-us',
			timezone='UTC',
		)
		cls.target_user.roles.add(cls.viewer_role)

		cls.order_management_manager_user = User.objects.create_user(
			username='order_manager_user',
			email='order-manager@example.com',
			password='OrderPass123!',
			first_name='Order',
			last_name='Manager',
			language_preference='en-us',
			timezone='UTC',
		)
		cls.order_management_manager_user.roles.add(cls.order_management_manager_role)

	def test_edit_page_renders_required_settings_fields(self):
		self.client.force_login(self.admin_user)

		response = self.client.get(reverse('accounts:user_edit', args=[self.target_user.pk]))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'name="language_preference"', html=False)
		self.assertContains(response, 'name="timezone"', html=False)
		self.assertContains(response, 'name="password1"', html=False)
		self.assertContains(response, 'name="must_change_password"', html=False)
		self.assertNotContains(response, 'name="division"', html=False)
		self.assertNotContains(response, 'name="managed_divisions"', html=False)

	def test_editing_self_keeps_session_and_password_when_blank(self):
		self.client.force_login(self.admin_user)

		response = self.client.post(
			reverse('accounts:user_edit', args=[self.admin_user.pk]),
			{
				'username': self.admin_user.username,
				'email': 'admin-updated@example.com',
				'first_name': 'Admin',
				'last_name': 'Updated',
				'employee_id': '',
				'phone_number': '',
				'department': '',
				'job_title': '',
				'company': '',
				'division': '',
				'manager': '',
				'roles': [],
				'managed_company': '',
				'managed_divisions': [],
				'managed_locations': [],
				'language_preference': 'en-us',
				'timezone': 'UTC',
				'is_active': 'on',
				'is_staff': 'on',
				'password1': '',
				'password2': '',
				'must_change_password': 'on',
			},
		)

		self.assertRedirects(response, reverse('accounts:user_list'))

		self.admin_user.refresh_from_db()
		self.assertEqual(self.admin_user.email, 'admin-updated@example.com')
		self.assertTrue(self.admin_user.check_password('AdminPass123!'))
		self.assertEqual(self.client.session.get('_auth_user_id'), str(self.admin_user.pk))

		list_response = self.client.get(reverse('accounts:user_list'))
		self.assertEqual(list_response.status_code, 200)

	def test_editing_another_user_does_not_switch_authenticated_session(self):
		self.client.force_login(self.admin_user)

		response = self.client.post(
			reverse('accounts:user_edit', args=[self.target_user.pk]),
			{
				'username': self.target_user.username,
				'email': 'target-updated@example.com',
				'first_name': 'Target',
				'last_name': 'Updated',
				'employee_id': '',
				'phone_number': '',
				'department': '',
				'job_title': '',
				'company': '',
				'division': '',
				'manager': '',
				'roles': [str(self.viewer_role.pk)],
				'managed_company': '',
				'managed_divisions': [],
				'managed_locations': [],
				'language_preference': 'en-us',
				'timezone': 'UTC',
				'is_active': 'on',
				'password1': '',
				'password2': '',
				'must_change_password': 'on',
			},
		)

		self.assertRedirects(response, reverse('accounts:user_list'))

		self.target_user.refresh_from_db()
		self.assertEqual(self.target_user.email, 'target-updated@example.com')
		self.assertTrue(self.target_user.check_password('TargetPass123!'))
		self.assertEqual(self.client.session.get('_auth_user_id'), str(self.admin_user.pk))

	def test_user_list_renders_order_management_access_scope(self):
		self.client.force_login(self.admin_user)

		response = self.client.get(reverse('accounts:user_list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Order management management and price approvals')
