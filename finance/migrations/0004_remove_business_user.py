# Generated by Django 5.1.4 on 2024-12-28 16:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0003_bankstatement_transaction_matched_statement_business_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='business',
            name='user',
        ),
    ]