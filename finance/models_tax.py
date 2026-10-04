"""
Nigerian Tax Engine — Models

Implements (from AMSS Architecture Section 8):
- TaxConfiguration: Business-level tax settings (VAT registered, CIT rate)
- TaxTransaction: Tax implications of individual financial transactions
- TaxReturn: Computed tax returns for a specific period
- TaxFilingDeadline: FIRS deadlines linked to the reminder engine
"""

from decimal import Decimal
from django.conf import settings
from django.db import models

from users.models import Business
from finance.models_accounting import Transaction


class TaxConfiguration(models.Model):
    """
    Business-specific tax configuration.
    Defines how the tax engine calculates liabilities for this business.
    """

    class FiscalYearEnd(models.IntegerChoices):
        JANUARY = 1, 'January 31'
        FEBRUARY = 2, 'February 28/29'
        MARCH = 3, 'March 31'
        APRIL = 4, 'April 30'
        MAY = 5, 'May 31'
        JUNE = 6, 'June 30'
        JULY = 7, 'July 31'
        AUGUST = 8, 'August 31'
        SEPTEMBER = 9, 'September 30'
        OCTOBER = 10, 'October 31'
        NOVEMBER = 11, 'November 30'
        DECEMBER = 12, 'December 31'

    business = models.OneToOneField(
        Business, on_delete=models.CASCADE, related_name='tax_config'
    )
    tin_number = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Tax Identification Number (TIN)'
    )
    is_vat_registered = models.BooleanField(
        default=False,
        help_text='If true, VAT is automatically calculated on sales'
    )
    vat_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('7.50'),
        help_text='Standard Nigerian VAT rate is 7.5%'
    )
    is_wht_agent = models.BooleanField(
        default=False,
        help_text='If true, business must deduct Withholding Tax from suppliers'
    )
    cit_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('20.00'),
        help_text='Corporate Income Tax rate (0% small, 20% medium, 30% large)'
    )
    fiscal_year_end = models.IntegerField(
        choices=FiscalYearEnd.choices, default=FiscalYearEnd.DECEMBER
    )
    tax_office = models.CharField(
        max_length=255, blank=True, default='',
        help_text='FIRS or State IRS office location'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Tax Config for {self.business}"


class TaxTransaction(models.Model):
    """
    Links a standard financial transaction to its tax implications.
    Used to build the running tax liability totals.
    """

    class TaxType(models.TextChoices):
        VAT = 'VAT', 'Value Added Tax (7.5%)'
        WHT = 'WHT', 'Withholding Tax'
        PAYE = 'PAYE', 'Pay As You Earn'
        CIT = 'CIT', 'Corporate Income Tax'
        EDT = 'EDT', 'Education Tax (3%)'
        OTHER = 'OTHER', 'Other Tax'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='tax_transactions'
    )
    transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name='tax_implications',
        null=True, blank=True
    )
    tax_type = models.CharField(max_length=10, choices=TaxType.choices)
    base_amount = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text='The amount upon which the tax is calculated'
    )
    tax_amount = models.DecimalField(max_digits=20, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    is_remitted = models.BooleanField(
        default=False,
        help_text='Whether this specific tax amount has been paid to the authority'
    )
    notes = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.tax_type}: ₦{self.tax_amount} on {self.date}"


class TaxReturn(models.Model):
    """
    A computed tax return for a specific period (e.g. Monthly VAT, Annual CIT).
    """

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        REVIEWED = 'REVIEWED', 'Reviewed'
        FILED = 'FILED', 'Filed'
        PAID = 'PAID', 'Paid'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='tax_returns'
    )
    tax_type = models.CharField(
        max_length=10, choices=TaxTransaction.TaxType.choices
    )
    period_start = models.DateField()
    period_end = models.DateField()
    total_liability = models.DecimalField(max_digits=20, decimal_places=2)
    total_paid = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.DRAFT
    )
    filing_date = models.DateField(null=True, blank=True)
    firs_receipt_number = models.CharField(
        max_length=100, blank=True, default=''
    )
    prepared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='prepared_tax_returns'
    )
    report_data_json = models.JSONField(
        default=dict, blank=True,
        help_text='The full calculated breakdown of this return'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-period_end']
        unique_together = ('business', 'tax_type', 'period_start', 'period_end')

    def __str__(self):
        return f"{self.tax_type} Return ({self.period_start} to {self.period_end})"


class TaxFilingDeadline(models.Model):
    """
    FIRS tax filing deadlines. Linked to the reminder engine.
    Example: VAT is due 21st of the following month.
    """

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='tax_deadlines'
    )
    tax_type = models.CharField(
        max_length=10, choices=TaxTransaction.TaxType.choices
    )
    period_name = models.CharField(
        max_length=100, help_text='e.g. March 2026 VAT'
    )
    deadline_date = models.DateField()
    is_filed = models.BooleanField(default=False)
    related_return = models.OneToOneField(
        TaxReturn, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='deadline'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deadline_date']

    def __str__(self):
        return f"{self.period_name} deadline: {self.deadline_date}"
