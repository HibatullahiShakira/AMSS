from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import models

from users.models import Business


CURRENCY_CHOICES = [
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),
    ('NGN', 'Nigeria Naira'),
    ('GBP', 'British Pound'),
    ('YEN', 'Yen'),
]


class Income(models.Model):
    SOURCE_CHOICES = [
        ('Sales', 'S'),
        ('Investment', 'I'),
        ('Loan', 'L'),
        ('Other', 'O'),
    ]

    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    source = models.CharField(max_length=15, choices=SOURCE_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    currency = models.CharField(max_length=15, choices=CURRENCY_CHOICES)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, default=1)

    class Meta:
        unique_together = ('user', 'date', 'source', 'description')

    def __str__(self):
        return f"Income: {self.currency}{self.amount} on {self.date}"


class Expense(models.Model):
    EXPENSE_CHOICES = [
        ('Rent', 'rent'),
        ('Utilities', 'utilities'),
        ('Salaries', 'salaries'),
        ('Office Supplies', 'office supplies'),
        ('Travel', 'travel'),
        ('Marketing', 'marketing'),
        ('Maintenance', 'maintenance'),
        ('Miscellaneous', 'miscellaneous')
    ]

    date = models.DateTimeField(auto_now_add=True)
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    expense_category = models.CharField(max_length=50, choices=EXPENSE_CHOICES)
    description = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    currency = models.CharField(max_length=15, choices=CURRENCY_CHOICES)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, default=1)

    class Meta:
        unique_together = ('user', 'date', 'expense_category', 'description')

    def __str__(self):
        return f"Expense {self.expense_category}: {self.currency}{self.amount} on {self.date}"


class Asset(models.Model):
    ASSET_TYPE = [
        ('Current', 'current'),
        ('Fixed', 'fixed'),
        ('Intangible', 'intangible'),
        ('Investment', 'investment'),
        ('Other', 'other'),
        ('Real Estate', 'real estate'),
        ('Land', 'land')
    ]

    VALUATION_METHOD = [
        ('Straight-Line', 'straight line'),
        ('Declining-Balance', 'declining-balance'),
        ('Units-of-Production', 'units-of-production'),
        ('Sum-of-the-Years-Digits', 'sum-of-the-years-digits'),
        ('Double-Declining-Balance', 'double-declining-balance'),
        ('Appreciation', 'appreciation')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField()
    amount = models.DecimalField(max_digits=20, decimal_places=2, blank=False, null=False)
    date_acquired = models.PositiveSmallIntegerField()
    asset_types = models.CharField(max_length=20, choices=ASSET_TYPE)
    depreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    appreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    useful_life = models.IntegerField(blank=False, null=False)
    residual_value = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=False, null=False)
    valuation_method = models.CharField(max_length=30, choices=VALUATION_METHOD, blank=False, null=False)
    is_appreciating = models.BooleanField(default=False)
    monthly_depreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    yearly_depreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    monthly_appreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    yearly_appreciation_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, default=1)

    def __str__(self):
        return f"{self.name} - {self.amount} ({self.asset_types})"

    def save(self, *args, **kwargs):
        amount = Decimal(str(self.amount))
        residual_value = Decimal(str(self.residual_value))
        useful_life = Decimal(str(self.useful_life))
        current_value = Decimal(str(self.current_value))
        date_acquired = Decimal(str(self.date_acquired))
        useful_life_int = int(str(self.useful_life))

        if self.is_appreciating:
            if not self.appreciation_rate:
                years = date.today().year - date_acquired
                if years > 0:
                    self.appreciation_rate = ((current_value - amount) / amount) * 100
                else:
                    self.appreciation_rate = Decimal(3.0)
            self.yearly_appreciation_rate = self.appreciation_rate
            self.monthly_appreciation_rate = self.appreciation_rate / 12
        else:
            if not self.depreciation_rate:
                if self.valuation_method == 'Straight-Line':
                    self.depreciation_rate = ((amount - residual_value) / useful_life) / amount * 100
                elif self.valuation_method == 'Declining-Balance':
                    self.depreciation_rate = (1 - (residual_value / amount) ** useful_life) * 100
                elif self.valuation_method == 'Units-of-Production':
                    self.depreciation_rate = ((amount - residual_value) / useful_life) * 100
                elif self.valuation_method == 'Sum-of-the-Years-Digits':
                    total_years = sum(range(1, useful_life_int + 1))
                    self.depreciation_rate = ((amount - residual_value) * (useful_life / total_years)) * 100
                elif self.valuation_method == 'Double-Declining-Balance':
                    self.depreciation_rate = (2 / useful_life) * 100
            self.yearly_depreciation_rate = self.depreciation_rate
            self.monthly_depreciation_rate = self.depreciation_rate / 12

        super(Asset, self).save(*args, **kwargs)
