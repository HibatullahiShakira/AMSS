"""
Asset Tracker — Enhanced Models

Adds to the existing Asset model:
- AssetMaintenanceLog: maintenance history tracking
- AssetDisposal: records asset disposal with gain/loss calculation
- DepreciationSchedule: pre-computed depreciation entries per period
"""

from decimal import Decimal
from django.conf import settings
from django.db import models

from users.models import Business


class AssetMaintenanceLog(models.Model):
    """
    Records maintenance activities performed on an asset.

    Tracks cost, who performed it, and next scheduled maintenance.
    Connected to the reminder engine for proactive maintenance alerts.
    """

    class MaintenanceType(models.TextChoices):
        PREVENTIVE = 'PREVENTIVE', 'Preventive'
        CORRECTIVE = 'CORRECTIVE', 'Corrective'
        ROUTINE = 'ROUTINE', 'Routine'
        EMERGENCY = 'EMERGENCY', 'Emergency'
        UPGRADE = 'UPGRADE', 'Upgrade'

    asset = models.ForeignKey(
        'finance.Asset', on_delete=models.CASCADE,
        related_name='maintenance_logs'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE,
        related_name='asset_maintenance_logs'
    )
    date = models.DateField()
    maintenance_type = models.CharField(
        max_length=15, choices=MaintenanceType.choices,
        default=MaintenanceType.ROUTINE
    )
    description = models.TextField()
    cost = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))
    performed_by = models.CharField(max_length=255, blank=True, default='')
    vendor = models.CharField(
        max_length=255, blank=True, default='',
        help_text='External vendor/service provider name'
    )
    next_maintenance_due = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='asset_maintenance_logs'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Maintenance: {self.asset.name} ({self.date}) — ₦{self.cost}"


class AssetDisposal(models.Model):
    """
    Records the disposal of a business asset.

    Calculates gain or loss on disposal:
    - Gain: proceeds > book value
    - Loss: proceeds < book value

    Disposal methods: Sale, Scrap, Donation, Trade-in, Write-off.
    """

    class DisposalMethod(models.TextChoices):
        SALE = 'SALE', 'Sale'
        SCRAP = 'SCRAP', 'Scrap'
        DONATION = 'DONATION', 'Donation'
        TRADE_IN = 'TRADE_IN', 'Trade-in'
        WRITE_OFF = 'WRITE_OFF', 'Write-off'
        INSURANCE_CLAIM = 'INSURANCE_CLAIM', 'Insurance Claim'

    asset = models.OneToOneField(
        'finance.Asset', on_delete=models.CASCADE,
        related_name='disposal'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE,
        related_name='asset_disposals'
    )
    date = models.DateField()
    method = models.CharField(
        max_length=20, choices=DisposalMethod.choices
    )
    proceeds = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00'),
        help_text='Amount received from disposal'
    )
    book_value_at_disposal = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text='Net book value of the asset at time of disposal'
    )
    gain_or_loss = models.DecimalField(
        max_digits=20, decimal_places=2,
        help_text='Positive = gain, Negative = loss'
    )
    buyer = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Buyer/recipient name (if applicable)'
    )
    reason = models.TextField(blank=True, default='')
    disposal_costs = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00'),
        help_text='Any costs associated with disposal (transport, cleaning, etc.)'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='asset_disposals'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return (
            f"Disposal: {self.asset.name} ({self.date}) — "
            f"{'Gain' if self.gain_or_loss >= 0 else 'Loss'}: ₦{abs(self.gain_or_loss)}"
        )

    def save(self, *args, **kwargs):
        # Auto-calculate gain/loss
        self.gain_or_loss = (
            self.proceeds - self.book_value_at_disposal - self.disposal_costs
        )
        super().save(*args, **kwargs)


class DepreciationSchedule(models.Model):
    """
    Pre-computed depreciation entry for a specific period.

    Generated when an asset is registered, showing the expected
    depreciation over its useful life. Follows Nigerian accounting
    standards (IFRS-based).

    Depreciation methods supported:
    - Straight-Line: equal amount each period
    - Reducing Balance: fixed % of remaining book value
    - Units of Production: based on usage
    """
    asset = models.ForeignKey(
        'finance.Asset', on_delete=models.CASCADE,
        related_name='depreciation_schedules'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE,
        related_name='depreciation_schedules'
    )
    period_number = models.PositiveIntegerField(
        help_text='Period number (1, 2, 3... for each year)'
    )
    period_start_date = models.DateField()
    period_end_date = models.DateField()
    opening_book_value = models.DecimalField(max_digits=20, decimal_places=2)
    depreciation_amount = models.DecimalField(max_digits=20, decimal_places=2)
    accumulated_depreciation = models.DecimalField(max_digits=20, decimal_places=2)
    closing_book_value = models.DecimalField(max_digits=20, decimal_places=2)
    is_posted = models.BooleanField(
        default=False,
        help_text='Whether this depreciation has been posted to the ledger'
    )
    journal_entry = models.ForeignKey(
        'finance.JournalEntry', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='depreciation_entries',
        help_text='The journal entry recording this depreciation'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['asset', 'period_number']
        unique_together = ('asset', 'period_number')

    def __str__(self):
        return (
            f"{self.asset.name} — Period {self.period_number}: "
            f"Dep ₦{self.depreciation_amount}, "
            f"Book Value ₦{self.closing_book_value}"
        )
