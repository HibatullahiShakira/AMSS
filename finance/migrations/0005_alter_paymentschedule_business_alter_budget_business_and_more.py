# Generated by Django 5.1.4 on 2024-12-28 16:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0004_remove_business_user'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentschedule',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='budget',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='income',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='expense',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='collateral',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='asset',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='creditor',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='equity',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='bankstatement',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.AlterField(
            model_name='liability',
            name='business',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='users.business'),
        ),
        migrations.DeleteModel(
            name='Business',
        ),
    ]
