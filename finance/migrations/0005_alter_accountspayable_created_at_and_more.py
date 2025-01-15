# Generated by Django 5.1.4 on 2025-01-14 13:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_rename_redicted_inflow_cashflowforecast_predicted_inflow_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountspayable',
            name='created_at',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='accountspayable',
            name='updated_at',
            field=models.DateField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='accountsreceivable',
            name='created_at',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='accountsreceivable',
            name='updated_at',
            field=models.DateField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='cashflowforecast',
            name='created_at',
            field=models.DateField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='cashflowforecast',
            name='updated_at',
            field=models.DateField(auto_now=True),
        ),
    ]
