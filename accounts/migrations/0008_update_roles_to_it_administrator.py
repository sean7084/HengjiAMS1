# Generated manually to update role choices

from django.db import migrations


def update_roles(apps, schema_editor):
    """
    Update existing user roles:
    - Convert 'manager' and 'it_specialist' to 'it_administrator'
    - Keep 'superadmin' and 'viewer' as is
    """
    User = apps.get_model('accounts', 'User')
    
    # Update managers to IT administrators
    User.objects.filter(admin_role='manager').update(admin_role='it_administrator')
    
    # Update IT specialists to IT administrators  
    User.objects.filter(admin_role='it_specialist').update(admin_role='it_administrator')


def reverse_update_roles(apps, schema_editor):
    """
    Reverse the role updates (convert back to original roles)
    """
    User = apps.get_model('accounts', 'User')
    
    # This is a one-way migration since we can't distinguish between
    # original managers and original IT specialists after the update
    # We'll convert all IT administrators back to IT specialists for safety
    User.objects.filter(admin_role='it_administrator').update(admin_role='it_specialist')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_auto_20250813_1656'),
    ]

    operations = [
        migrations.RunPython(update_roles, reverse_update_roles),
    ]
