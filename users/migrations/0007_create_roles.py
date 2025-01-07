from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Owner')
    Group.objects.get_or_create(name='Manager')
    Group.objects.get_or_create(name='Employee')


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0006_user_address_user_age_user_phone_number'),
    ]

    operations = [
        migrations.RunPython(create_roles),
    ]
