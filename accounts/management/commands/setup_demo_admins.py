"""
Management command to set up demo admin users with different roles.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from companies.models import Company, Division, Location

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up demo admin users with different roles'

    def handle(self, *args, **options):
        self.stdout.write('Setting up demo admin users...')
        
        # Set existing admin as superadmin
        try:
            admin_user = User.objects.get(username='admin')
            admin_user.admin_role = User.AdminRole.SUPERADMIN
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated admin user to Superadmin'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('Admin user not found'))
        
        # Create sample companies if they don't exist
        company1, created = Company.objects.get_or_create(
            code='ACME',
            defaults={
                'name': 'ACME Corporation',
                'description': 'Technology company specializing in software solutions',
                'email': 'contact@acme.com',
                'phone_number': '+1-555-0123',
                'address_line1': '123 Tech Street',
                'city': 'San Francisco',
                'state_province': 'CA',
                'postal_code': '94105',
                'country': 'United States'
            }
        )
        
        company2, created = Company.objects.get_or_create(
            code='GLOB',
            defaults={
                'name': 'Global Industries',
                'description': 'Manufacturing and logistics company',
                'email': 'info@global.com',
                'phone_number': '+1-555-0456',
                'address_line1': '456 Industrial Ave',
                'city': 'Chicago',
                'state_province': 'IL',
                'postal_code': '60601',
                'country': 'United States'
            }
        )
        
        # Create divisions
        it_division, created = Division.objects.get_or_create(
            company=company1,
            code='IT',
            defaults={
                'name': 'Information Technology',
                'description': 'IT department handling all technology needs'
            }
        )
        
        hr_division, created = Division.objects.get_or_create(
            company=company1,
            code='HR',
            defaults={
                'name': 'Human Resources',
                'description': 'HR department handling personnel and administration'
            }
        )
        
        ops_division, created = Division.objects.get_or_create(
            company=company2,
            code='OPS',
            defaults={
                'name': 'Operations',
                'description': 'Operations department handling manufacturing'
            }
        )
        
        # Create locations
        sf_office, created = Location.objects.get_or_create(
            company=company1,
            division=it_division,
            code='SF-HQ',
            defaults={
                'name': 'San Francisco Headquarters',
                'location_type': Location.LocationType.OFFICE,
                'address_line1': '123 Tech Street',
                'city': 'San Francisco',
                'state_province': 'CA',
                'postal_code': '94105',
                'country': 'United States'
            }
        )
        
        chicago_warehouse, created = Location.objects.get_or_create(
            company=company2,
            division=ops_division,
            code='CHI-WH',
            defaults={
                'name': 'Chicago Warehouse',
                'location_type': Location.LocationType.WAREHOUSE,
                'address_line1': '456 Industrial Ave',
                'city': 'Chicago',
                'state_province': 'IL',
                'postal_code': '60601',
                'country': 'United States'
            }
        )
        
        # Create Manager admin
        manager_user, created = User.objects.get_or_create(
            username='manager1',
            defaults={
                'email': 'manager@acme.com',
                'first_name': 'John',
                'last_name': 'Manager',
                'admin_role': User.AdminRole.MANAGER,
                'is_active': True,
                'is_staff': True
            }
        )
        if created:
            manager_user.set_password('manager123')
            manager_user.save()
        manager_user.managed_company = company1
        manager_user.save()
        self.stdout.write(self.style.SUCCESS(f'Created Manager: {manager_user.username}'))
        
        # Create IT Specialist admin
        it_specialist, created = User.objects.get_or_create(
            username='itspecialist1',
            defaults={
                'email': 'it@acme.com',
                'first_name': 'Alice',
                'last_name': 'Tech',
                'admin_role': User.AdminRole.IT_SPECIALIST,
                'is_active': True,
                'is_staff': True
            }
        )
        if created:
            it_specialist.set_password('itspec123')
            it_specialist.save()
        it_specialist.managed_divisions.set([it_division, hr_division])
        self.stdout.write(self.style.SUCCESS(f'Created IT Specialist: {it_specialist.username}'))
        
        # Create Viewer admin
        viewer_user, created = User.objects.get_or_create(
            username='viewer1',
            defaults={
                'email': 'viewer@global.com',
                'first_name': 'Bob',
                'last_name': 'Observer',
                'admin_role': User.AdminRole.VIEWER,
                'is_active': True,
                'is_staff': True
            }
        )
        if created:
            viewer_user.set_password('viewer123')
            viewer_user.save()
        viewer_user.managed_locations.set([chicago_warehouse])
        self.stdout.write(self.style.SUCCESS(f'Created Viewer: {viewer_user.username}'))
        
        self.stdout.write(self.style.SUCCESS('\nDemo admin users created successfully!'))
        self.stdout.write('Users created:')
        self.stdout.write(f'  - admin (superadmin): full access')
        self.stdout.write(f'  - manager1 (manager): access to ACME Corporation')
        self.stdout.write(f'  - itspecialist1 (IT specialist): access to IT and HR divisions')
        self.stdout.write(f'  - viewer1 (viewer): read-only access to Chicago Warehouse')
