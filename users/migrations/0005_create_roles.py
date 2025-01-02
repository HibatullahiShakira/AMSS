from django.db import migrations


def create_roles(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.get_or_create(name='Owner')
    Group.objects.get_or_create(name='Admin')
    Group.objects.get_or_create(name='Manager')
    Group.objects.get_or_create(name='Employee')


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0004_remove_business_is_verified_and_more'),
    ]

    operations = [
        migrations.RunPython(create_roles),
    ]
