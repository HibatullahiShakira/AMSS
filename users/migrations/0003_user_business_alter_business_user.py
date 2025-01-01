# Generated by Django 5.1.4 on 2024-12-30 05:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_business_is_verified_business_verification_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='business',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='owner', to='users.business'),
        ),
        migrations.AlterField(
            model_name='business',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='business_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]