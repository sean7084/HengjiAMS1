"""
Management command to create sample assets for testing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from datetime import datetime, timedelta

from assets.models import Asset, AssetCategory, AssetBrand, AssetModel, AssetAssignment
from companies.models import Company, Division, Location
from accounts.models import User


class Command(BaseCommand):
    help = 'Create sample assets for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample assets to create (default: 20)'
        )

    def handle(self, *args, **options):
        count = options['count']
        self.stdout.write(self.style.SUCCESS(f'Creating {count} sample assets...'))

        # Sample data
        asset_types = [
            'Laptop', 'Desktop Computer', 'Monitor', 'Printer', 'Scanner',
            'Server', 'Network Switch', 'Router', 'Tablet', 'Smartphone',
            'Projector', 'Camera', 'Hard Drive', 'UPS', 'Keyboard',
            'Mouse', 'Webcam', 'Headset', 'Speaker', 'Microphone'
        ]

        manufacturers = [
            'Dell', 'HP', 'Lenovo', 'Apple', 'Asus', 'Acer', 'Samsung',
            'LG', 'Sony', 'Canon', 'Epson', 'Cisco', 'Microsoft', 'Logitech'
        ]

        models_by_type = {
            'Laptop': ['ThinkPad X1', 'MacBook Pro', 'EliteBook 840', 'Inspiron 15', 'XPS 13'],
            'Desktop Computer': ['OptiPlex 7090', 'ThinkCentre M90', 'Mac Mini', 'Pavilion', 'Vostro 3681'],
            'Monitor': ['UltraSharp U2720Q', 'ThinkVision P27', 'Studio Display', 'ProDisplay XDR', 'Odyssey G7'],
            'Printer': ['LaserJet Pro M404', 'OfficeJet Pro 9015', 'EcoTank ET-2760', 'Color LaserJet Pro M255'],
            'Server': ['PowerEdge R740', 'ThinkSystem SR650', 'Mac Pro', 'ProLiant DL380'],
        }

        # Get existing companies and users
        companies = list(Company.objects.all())
        divisions = list(Division.objects.all())
        locations = list(Location.objects.all())
        users = list(User.objects.all())

        # Create some categories and brands if they don't exist
        categories = []
        category_names = ['IT Equipment', 'Office Equipment', 'Network Equipment', 'Mobile Devices', 'Audio/Visual']
        for cat_name in category_names:
            category, created = AssetCategory.objects.get_or_create(
                name=cat_name,
                defaults={
                    'code': cat_name.upper().replace(' ', '_'),
                    'description': f'{cat_name} category'
                }
            )
            categories.append(category)

        # Create some brands if they don't exist
        brands = []
        for manufacturer in manufacturers:
            brand, created = AssetBrand.objects.get_or_create(
                name=manufacturer,
                defaults={
                    'code': manufacturer.upper()[:10],  # Truncate to fit field
                    'description': f'{manufacturer} brand'
                }
            )
            brands.append(brand)

        created_count = 0
        for i in range(count):
            # Random asset type and details
            asset_type = random.choice(asset_types)
            manufacturer = random.choice(manufacturers)
            
            # Get model based on type if available, otherwise generate generic
            if asset_type in models_by_type:
                model = random.choice(models_by_type[asset_type])
            else:
                model = f'{asset_type} {random.randint(1000, 9999)}'

            # Generate asset number and serial number (avoid collisions)
            existing_numbers = set(Asset.objects.values_list('asset_number', flat=True))
            counter = 1
            while True:
                asset_number = f'AMS{str(counter).zfill(6)}'
                if asset_number not in existing_numbers:
                    break
                counter += 1
            
            serial_number = f'{manufacturer[:3].upper()}{random.randint(100000, 999999)}'
            barcode = f'BC{str(counter).zfill(8)}'  # Unique barcode

            # Random category and brand
            category = random.choice(categories)
            brand = random.choice(brands)

            # Random company/division/location - company is required
            if not companies:
                self.stdout.write(self.style.ERROR('No companies found. Please create companies first.'))
                return
            
            company = random.choice(companies)
            division = random.choice(divisions) if divisions else None
            location = random.choice(locations) if locations else None

            # Random purchase details
            purchase_date = timezone.now().date() - timedelta(days=random.randint(30, 1095))  # 1 month to 3 years ago
            purchase_price = Decimal(str(random.randint(500, 5000)))

            # Random status
            status_choices = [choice[0] for choice in Asset.AssetStatus.choices]
            status = random.choice(status_choices)

            try:
                # Create asset
                asset = Asset.objects.create(
                    asset_number=asset_number,
                    name=f'{manufacturer} {model}',
                    serial_number=serial_number,
                    barcode=barcode,
                    category=category,
                    brand=brand,
                    status=status,
                    company=company,
                    division=division,
                    location=location,
                    purchase_date=purchase_date,
                    purchase_price=purchase_price,
                    description=f'{asset_type} - {manufacturer} {model}',
                )

                # Randomly assign some assets to users
                if users and random.choice([True, False, False]):  # 33% chance of assignment
                    user = random.choice(users)
                    AssetAssignment.objects.create(
                        asset=asset,
                        assignment_type=AssetAssignment.AssignmentType.USER,
                        assigned_to=user,
                        notes=f'Assigned to {user.get_display_name()} for testing'
                    )
                    asset.status = Asset.AssetStatus.IN_USE
                    asset.save()

                created_count += 1
                self.stdout.write(f'Created asset: {asset.name} ({asset.serial_number})')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create asset {i+1}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample assets!')
        )
