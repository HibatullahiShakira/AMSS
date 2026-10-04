"""
Expense & Reminder Engine — Models

Implements (from AMSS Architecture Section 6):
- RecurringExpense: Tracks recurring obligations (rent, utilities, salaries)
  with frequency, next_due_date, auto-escalation rate.
- ExpenseCategory: Extended categorisation with macro-correlation fields.
- Reminder: Intelligent reminder with materiality scoring, coverage ratio,
  urgency level, and escalation history.
- ReminderLog: Audit trail of sent reminders and acknowledgements.
"""

from decimal import Decimal
from django.conf import settings
from django.db import models

from users.models import Business


class ExpenseCategory(models.Model):
    """
    Extended expense categories with macro-economic correlation.

    Each category can be linked to a macro indicator (e.g. Diesel expense
    correlates with FX rate) for anomaly detection and intelligence.
    """

    MACRO_CORRELATION_CHOICES = [
        ('NONE', 'No Macro Correlation'),
        ('FX_USD', 'USD/NGN Exchange Rate'),
        ('DIESEL', 'Diesel Price Index'),
        ('INFLATION', 'CPI Inflation Rate'),
        ('ENERGY', 'Energy Price Index'),
        ('INTEREST', 'Interest Rate'),
    ]

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='expense_categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    is_deductible = models.BooleanField(
        default=True,
        help_text='Whether this expense is tax-deductible'
    )
    macro_correlation = models.CharField(
        max_length=20, choices=MACRO_CORRELATION_CHOICES,
        default='NONE',
        help_text='Which macro indicator this expense category correlates with'
    )
    budget_limit_monthly = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True,
        help_text='Monthly budget cap for this category (optional)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('business', 'name')
        ordering = ['name']
        verbose_name_plural = 'Expense categories'

    def __str__(self):
        return f"{self.name} ({self.business})"


class RecurringExpense(models.Model):
    """
    Tracks recurring financial obligations.

    Per architecture Section 6: rent, utilities, salaries, subscriptions,
    loan repayments — anything that recurs on a schedule. Linked to the
    reminder engine for proactive alerts.
    """

    class Frequency(models.TextChoices):
        DAILY = 'DAILY', 'Daily'
        WEEKLY = 'WEEKLY', 'Weekly'
        BIWEEKLY = 'BIWEEKLY', 'Bi-Weekly'
        MONTHLY = 'MONTHLY', 'Monthly'
        QUARTERLY = 'QUARTERLY', 'Quarterly'
        SEMI_ANNUALLY = 'SEMI_ANNUALLY', 'Semi-Annually'
        ANNUALLY = 'ANNUALLY', 'Annually'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        PAUSED = 'PAUSED', 'Paused'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='recurring_expenses'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='recurring_expenses'
    )
    name = models.CharField(max_length=255, help_text='e.g. Office Rent, DSTV Subscription')
    description = models.TextField(blank=True, default='')
    category = models.ForeignKey(
        ExpenseCategory, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='recurring_expenses'
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    frequency = models.CharField(
        max_length=15, choices=Frequency.choices, default=Frequency.MONTHLY
    )
    next_due_date = models.DateField(
        help_text='The next date this expense is due'
    )
    start_date = models.DateField(
        help_text='When this recurring expense started'
    )
    end_date = models.DateField(
        null=True, blank=True,
        help_text='When this recurring expense ends (null = indefinite)'
    )
    auto_escalation_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('0.00'),
        help_text='Annual escalation rate in % (e.g. rent increases 10% yearly)'
    )
    last_escalation_date = models.DateField(null=True, blank=True)
    payee = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Who receives this payment (landlord, utility company, etc.)'
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.ACTIVE
    )
    total_paid = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    payment_count = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['next_due_date']

    def __str__(self):
        return f"{self.name} — {self.currency} {self.amount} ({self.frequency})"


class Reminder(models.Model):
    """
    Intelligent reminder with materiality scoring and urgency-based escalation.

    Per architecture Section 6.2: The reminder engine computes materiality
    (obligation_amount / monthly_revenue), checks cash coverage, determines
    lead time, chooses channel, and escalates if unacknowledged.
    """

    class UrgencyLevel(models.TextChoices):
        CRITICAL = 'CRITICAL', 'Critical'
        URGENT = 'URGENT', 'Urgent'
        NORMAL = 'NORMAL', 'Normal'
        LOW = 'LOW', 'Low'

    class ReminderStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        SNOOZED = 'SNOOZED', 'Snoozed'
        OVERDUE = 'OVERDUE', 'Overdue'
        COMPLETED = 'COMPLETED', 'Completed'

    class ReminderType(models.TextChoices):
        RECURRING_EXPENSE = 'RECURRING_EXPENSE', 'Recurring Expense'
        LIABILITY_PAYMENT = 'LIABILITY_PAYMENT', 'Liability Payment'
        TAX_FILING = 'TAX_FILING', 'Tax Filing'
        INVOICE_FOLLOWUP = 'INVOICE_FOLLOWUP', 'Invoice Follow-up'
        CUSTOM = 'CUSTOM', 'Custom'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='reminders'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='reminders'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    reminder_type = models.CharField(
        max_length=20, choices=ReminderType.choices, default=ReminderType.CUSTOM
    )
    due_date = models.DateField()
    amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00'),
        help_text='The financial obligation amount associated with this reminder'
    )
    currency = models.CharField(max_length=10, default='NGN')

    # Intelligence fields (computed by helpers_expense.py)
    materiality_score = models.DecimalField(
        max_digits=6, decimal_places=4, default=Decimal('0.00'),
        help_text='obligation_amount / monthly_revenue'
    )
    coverage_ratio = models.DecimalField(
        max_digits=6, decimal_places=4, default=Decimal('0.00'),
        help_text='current_cash / obligation_amount'
    )
    urgency_level = models.CharField(
        max_length=10, choices=UrgencyLevel.choices, default=UrgencyLevel.NORMAL
    )
    status = models.CharField(
        max_length=15, choices=ReminderStatus.choices, default=ReminderStatus.PENDING
    )

    # Linked objects (optional — a reminder can be linked to a specific source)
    recurring_expense = models.ForeignKey(
        RecurringExpense, on_delete=models.CASCADE,
        null=True, blank=True, related_name='reminders'
    )
    liability = models.ForeignKey(
        'finance.Liability', on_delete=models.CASCADE,
        null=True, blank=True, related_name='reminders'
    )

    # Scheduling
    snooze_until = models.DateTimeField(null=True, blank=True)
    escalation_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', '-urgency_level']

    def __str__(self):
        return f"[{self.urgency_level}] {self.title} — due {self.due_date}"


class ReminderLog(models.Model):
    """
    Audit trail for reminder delivery and acknowledgement.
    """

    class Channel(models.TextChoices):
        IN_APP = 'IN_APP', 'In-App Notification'
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'
        WHATSAPP = 'WHATSAPP', 'WhatsApp'

    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        SENT = 'SENT', 'Sent'
        DELIVERED = 'DELIVERED', 'Delivered'
        ACKNOWLEDGED = 'ACKNOWLEDGED', 'Acknowledged'
        SNOOZED = 'SNOOZED', 'Snoozed'
        ESCALATED = 'ESCALATED', 'Escalated'

    reminder = models.ForeignKey(
        Reminder, on_delete=models.CASCADE, related_name='logs'
    )
    action = models.CharField(max_length=15, choices=Action.choices)
    channel = models.CharField(
        max_length=10, choices=Channel.choices,
        default=Channel.IN_APP
    )
    message = models.TextField(blank=True, default='')
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action} — {self.reminder.title} via {self.channel}"
