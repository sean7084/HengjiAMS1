from django.db import migrations


LEGACY_ROLE = (
    'order_management_procurement_specialist',
    'Order Management & Procurement Specialist',
    'Order management and procurement workflow access.',
)

MANAGER_ROLE = (
    'order_management_manager',
    'Order Management Manager',
    'Full order management access, including live price changes, approvals, and imports.',
)

SPECIALIST_ROLE = (
    'order_management_specialist',
    'Order Management Specialist',
    'Order management workflow access with manager approval required for price list changes.',
)


def _ensure_role(AdminRole, role_definition):
    code, name, description = role_definition
    role, _created = AdminRole.objects.update_or_create(
        code=code,
        defaults={
            'name': name,
            'description': description,
            'is_active': True,
        },
    )
    return role


def forwards(apps, schema_editor):
    AdminRole = apps.get_model('accounts', 'AdminRole')
    User = apps.get_model('accounts', 'User')

    legacy_code, manager_name, manager_description = MANAGER_ROLE[0], MANAGER_ROLE[1], MANAGER_ROLE[2]
    legacy_role = AdminRole.objects.filter(code=LEGACY_ROLE[0]).first()
    manager_role = AdminRole.objects.filter(code=MANAGER_ROLE[0]).first()

    if legacy_role and manager_role and legacy_role.pk != manager_role.pk:
        for user in User.objects.filter(roles=legacy_role).distinct():
            user.roles.add(manager_role)
            user.roles.remove(legacy_role)
        legacy_role.delete()
    elif legacy_role and not manager_role:
        legacy_role.code = legacy_code
        legacy_role.name = manager_name
        legacy_role.description = manager_description
        legacy_role.is_active = True
        legacy_role.save(update_fields=['code', 'name', 'description', 'is_active'])
        manager_role = legacy_role

    manager_role = manager_role or _ensure_role(AdminRole, MANAGER_ROLE)
    manager_role.name = manager_name
    manager_role.description = manager_description
    manager_role.is_active = True
    manager_role.save(update_fields=['name', 'description', 'is_active'])

    _ensure_role(AdminRole, SPECIALIST_ROLE)


def backwards(apps, schema_editor):
    AdminRole = apps.get_model('accounts', 'AdminRole')
    User = apps.get_model('accounts', 'User')

    legacy_role = AdminRole.objects.filter(code=LEGACY_ROLE[0]).first()
    manager_role = AdminRole.objects.filter(code=MANAGER_ROLE[0]).first()
    specialist_role = AdminRole.objects.filter(code=SPECIALIST_ROLE[0]).first()

    if manager_role and not legacy_role:
        manager_role.code = LEGACY_ROLE[0]
        manager_role.name = LEGACY_ROLE[1]
        manager_role.description = LEGACY_ROLE[2]
        manager_role.is_active = True
        manager_role.save(update_fields=['code', 'name', 'description', 'is_active'])
        legacy_role = manager_role

    legacy_role = legacy_role or _ensure_role(AdminRole, LEGACY_ROLE)

    for role in [manager_role, specialist_role]:
        if not role or role.pk == legacy_role.pk:
            continue
        for user in User.objects.filter(roles=role).distinct():
            user.roles.add(legacy_role)
            user.roles.remove(role)
        role.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0015_receivedemailmessage_rfq_confidence_and_more'),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]