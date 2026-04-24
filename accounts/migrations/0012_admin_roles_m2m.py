from django.db import migrations, models


ROLE_DEFAULTS = [
    ('superadmin', 'Superadmin', 'Full system access across all modules and companies.'),
    ('it_administrator', 'IT Administrator', 'Asset and audit administration with scoped company and division access.'),
    ('viewer', 'Viewer', 'Read-only visibility scoped to assigned locations.'),
    ('order_management_procurement_specialist', 'Order Management & Procurement Specialist', 'Order management and procurement workflow access.'),
]


def seed_admin_roles(apps, schema_editor):
    AdminRole = apps.get_model('accounts', 'AdminRole')
    for code, name, description in ROLE_DEFAULTS:
        AdminRole.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'description': description,
                'is_active': True,
            },
        )


def unseed_admin_roles(apps, schema_editor):
    AdminRole = apps.get_model('accounts', 'AdminRole')
    AdminRole.objects.filter(code__in=[code for code, _name, _description in ROLE_DEFAULTS]).delete()


def migrate_user_roles_forward(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    AdminRole = apps.get_model('accounts', 'AdminRole')

    role_map = {role.code: role for role in AdminRole.objects.all()}
    legacy_role_map = {
        'manager': 'it_administrator',
        'it_specialist': 'it_administrator',
    }

    for user in User.objects.exclude(admin_role__isnull=True).exclude(admin_role=''):
        mapped_code = legacy_role_map.get(user.admin_role, user.admin_role)
        role = role_map.get(mapped_code)
        if role:
            user.roles.add(role)


def migrate_user_roles_reverse(apps, schema_editor):
    User = apps.get_model('accounts', 'User')

    role_priority = [
        'superadmin',
        'it_administrator',
        'viewer',
        'order_management_procurement_specialist',
    ]

    for user in User.objects.all():
        assigned_codes = list(user.roles.values_list('code', flat=True))
        selected_code = ''
        for role_code in role_priority:
            if role_code in assigned_codes:
                selected_code = role_code
                break
        if not selected_code and assigned_codes:
            selected_code = assigned_codes[0]
        user.admin_role = selected_code
        user.save(update_fields=['admin_role'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0011_normalize_language_preference_codes'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=64, unique=True, verbose_name='Role Code')),
                ('name', models.CharField(max_length=120, verbose_name='Role Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Administrator Role',
                'verbose_name_plural': 'Administrator Roles',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='roles',
            field=models.ManyToManyField(blank=True, help_text='Roles for administrator access levels', related_name='users', to='accounts.adminrole', verbose_name='Administrator Roles'),
        ),
        migrations.RunPython(seed_admin_roles, unseed_admin_roles),
        migrations.RunPython(migrate_user_roles_forward, migrate_user_roles_reverse),
        migrations.RemoveField(
            model_name='user',
            name='admin_role',
        ),
    ]