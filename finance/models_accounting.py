"""
Core Accounting Models — Double-Entry Ledger System

Implements the AMSS Enterprise double-entry accounting foundation:
- Chart of Accounts (hierarchical account structure)
- Journal Entries with debit/credit lines (enforces balance)
- Transactions (links journal entries to real-world movements)
- Bank Accounts and Statements
- Reconciliation Sessions

All models are multi-tenant via the `business` ForeignKey.
"""

from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum

from users.models import Business


class AccountType(models.TextChoices):
    """Standard accounting equation: Assets = Liabilities + Equity + (Revenue - Expenses)"""
    ASSET = 'ASSET', 'Asset'
    LIABILITY = 'LIABILITY', 'Liability'
    EQUITY = 'EQUITY', 'Equity'
    REVENUE = 'REVENUE', 'Revenue'
    EXPENSE = 'EXPENSE', 'Expense'


class Account(models.Model):
    """
    Chart of Accounts — hierarchical account structure.

    Each business has its own chart of accounts. Accounts can be nested
    (e.g. Assets > Current Assets > Cash) via the `parent` self-FK.

    Account codes follow Nigerian accounting conventions:
    - 1xxx: Assets
    - 2xxx: Liabilities
    - 3xxx: Equity
    - 4xxx: Revenue
    - 5xxx: Expenses
    """
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='accounts'
    )
    code = models.CharField(
        max_length=20,
        help_text='Account code (e.g. 1000 for Cash)'
    )
    name = models.CharField(max_length=255)
    account_type = models.CharField(
        max_length=20, choices=AccountType.choices
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children',
        help_text='Parent account for hierarchical chart of accounts'
    )
    description = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True)
    is_system_account = models.BooleanField(
        default=False,
        help_text='System accounts cannot be deleted (e.g. default Cash, AR, AP)'
    )
    currency = models.CharField(max_length=10, default='NGN')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business', 'code')
        ordering = ['code']

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def balance(self):
        """
        Calculate the current balance of this account.

        Debit-normal accounts (Asset, Expense): balance = total_debits - total_credits
        Credit-normal accounts (Liability, Equity, Revenue): balance = total_credits - total_debits
        """
        totals = self.journal_lines.filter(
            journal_entry__status=JournalEntry.Status.POSTED
        ).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        total_debit = totals['total_debit'] or Decimal('0.00')
        total_credit = totals['total_credit'] or Decimal('0.00')

        if self.account_type in [AccountType.ASSET, AccountType.EXPENSE]:
            return total_debit - total_credit
        else:
            return total_credit - total_debit


class JournalEntry(models.Model):
    """
    A journal entry is the fundamental unit of double-entry accounting.

    Every journal entry must have at least two lines, and the sum of all
    debit amounts must equal the sum of all credit amounts.

    Status workflow: DRAFT → POSTED (or VOID)
    Only POSTED entries affect account balances.
    """

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        POSTED = 'POSTED', 'Posted'
        VOID = 'VOID', 'Void'

    class EntryType(models.TextChoices):
        STANDARD = 'STANDARD', 'Standard'
        ADJUSTING = 'ADJUSTING', 'Adjusting'
        CLOSING = 'CLOSING', 'Closing'
        REVERSING = 'REVERSING', 'Reversing'
        AUTO_GENERATED = 'AUTO', 'Auto-Generated'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='journal_entries'
    )
    date = models.DateField()
    reference_number = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Unique reference (auto-generated if blank)'
    )
    description = models.TextField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    entry_type = models.CharField(
        max_length=10, choices=EntryType.choices, default=EntryType.STANDARD
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='journal_entries_created'
    )
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='journal_entries_posted'
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='journal_entries_voided'
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    void_reason = models.TextField(blank=True, default='')
    source_module = models.CharField(
        max_length=50, blank=True, default='',
        help_text='Which module created this entry (e.g. finance, billing, asset)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal entries'

    def __str__(self):
        return f"JE-{self.reference_number or self.pk} ({self.date}) — {self.description[:50]}"

    def clean(self):
        """Validate that the journal entry balances (debits == credits)."""
        if self.pk:
            totals = self.lines.aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount')
            )
            total_debit = totals['total_debit'] or Decimal('0.00')
            total_credit = totals['total_credit'] or Decimal('0.00')

            if total_debit != total_credit:
                raise ValidationError(
                    f'Journal entry does not balance. '
                    f'Debits: {total_debit}, Credits: {total_credit}'
                )

    @property
    def is_balanced(self):
        """Check if total debits equal total credits."""
        totals = self.lines.aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount')
        )
        total_debit = totals['total_debit'] or Decimal('0.00')
        total_credit = totals['total_credit'] or Decimal('0.00')
        return total_debit == total_credit

    @property
    def total_amount(self):
        """The total debit (or credit) amount of this entry."""
        return self.lines.aggregate(
            total=Sum('debit_amount')
        )['total'] or Decimal('0.00')

    def generate_reference_number(self):
        """Auto-generate a reference number if none provided."""
        if not self.reference_number:
            last_entry = JournalEntry.objects.filter(
                business=self.business
            ).order_by('-pk').first()
            next_num = (last_entry.pk + 1) if last_entry else 1
            self.reference_number = f"JE-{self.business.pk}-{next_num:06d}"

    def save(self, *args, **kwargs):
        self.generate_reference_number()
        super().save(*args, **kwargs)


class JournalEntryLine(models.Model):
    """
    A single line in a journal entry — either a debit or a credit to an account.

    Rules:
    - Each line must have EITHER a debit_amount OR a credit_amount (not both, not neither)
    - The account's balance is affected only when the parent JournalEntry is POSTED
    """
    journal_entry = models.ForeignKey(
        JournalEntry, on_delete=models.CASCADE, related_name='lines'
    )
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name='journal_lines'
    )
    debit_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    credit_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    description = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        ordering = ['pk']

    def __str__(self):
        if self.debit_amount > 0:
            return f"DR {self.account.code}: {self.debit_amount}"
        return f"CR {self.account.code}: {self.credit_amount}"

    def clean(self):
        """Validate that exactly one of debit or credit is non-zero."""
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValidationError(
                'A journal line cannot have both debit and credit amounts.'
            )
        if self.debit_amount == 0 and self.credit_amount == 0:
            raise ValidationError(
                'A journal line must have either a debit or credit amount.'
            )
        if self.debit_amount < 0 or self.credit_amount < 0:
            raise ValidationError('Amounts cannot be negative.')


class Transaction(models.Model):
    """
    A Transaction represents a real-world financial movement linked to a journal entry.

    This bridges the accounting layer with the operational layer — an invoice payment,
    a bank transfer, a cash receipt, etc.
    """

    class TransactionType(models.TextChoices):
        INCOME = 'INCOME', 'Income'
        EXPENSE = 'EXPENSE', 'Expense'
        TRANSFER = 'TRANSFER', 'Transfer'
        JOURNAL = 'JOURNAL', 'Journal Adjustment'
        LOAN_DISBURSEMENT = 'LOAN_DISBURSEMENT', 'Loan Disbursement'
        LOAN_REPAYMENT = 'LOAN_REPAYMENT', 'Loan Repayment'
        ASSET_PURCHASE = 'ASSET_PURCHASE', 'Asset Purchase'
        ASSET_DISPOSAL = 'ASSET_DISPOSAL', 'Asset Disposal'
        TAX_PAYMENT = 'TAX_PAYMENT', 'Tax Payment'

    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer'
        POS = 'POS', 'POS'
        CHEQUE = 'CHEQUE', 'Cheque'
        MOBILE_MONEY = 'MOBILE_MONEY', 'Mobile Money'
        USSD = 'USSD', 'USSD'
        CARD = 'CARD', 'Card'
        OTHER = 'OTHER', 'Other'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='transactions'
    )
    journal_entry = models.OneToOneField(
        JournalEntry, on_delete=models.CASCADE, related_name='transaction',
        null=True, blank=True
    )
    transaction_type = models.CharField(
        max_length=20, choices=TransactionType.choices
    )
    amount = models.DecimalField(max_digits=20, decimal_places=2)
    currency = models.CharField(max_length=10, default='NGN')
    date = models.DateField()
    description = models.CharField(max_length=500)
    payment_method = models.CharField(
        max_length=20, choices=PaymentMethod.choices,
        default=PaymentMethod.BANK_TRANSFER
    )
    external_reference = models.CharField(
        max_length=255, blank=True, default='',
        help_text='External reference (bank ref, POS terminal ID, etc.)'
    )
    is_reconciled = models.BooleanField(default=False)
    counterparty = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Name of the other party (customer, supplier, bank)'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='transactions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.transaction_type}: {self.currency} {self.amount} ({self.date})"


class BankAccount(models.Model):
    """
    A business's bank account — used for bank reconciliation.
    """
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='bank_accounts'
    )
    account_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=20)
    sort_code = models.CharField(max_length=20, blank=True, default='')
    current_balance = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    currency = models.CharField(max_length=10, default='NGN')
    is_active = models.BooleanField(default=True)
    linked_account = models.ForeignKey(
        Account, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='bank_accounts',
        help_text='The Chart of Accounts entry this bank account maps to'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('business', 'account_number', 'bank_name')

    def __str__(self):
        return f"{self.bank_name} — {self.account_number} ({self.account_name})"


class BankStatement(models.Model):
    """
    Individual bank statement line — imported from bank or entered manually.
    Used for reconciliation against system transactions.
    """
    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='statements'
    )
    transaction_date = models.DateField()
    value_date = models.DateField(null=True, blank=True)
    description = models.CharField(max_length=500)
    reference = models.CharField(max_length=255, blank=True, default='')
    debit_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    credit_amount = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00')
    )
    running_balance = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    is_reconciled = models.BooleanField(default=False)
    matched_transaction = models.ForeignKey(
        Transaction, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='matched_statements'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        amount = self.credit_amount if self.credit_amount > 0 else -self.debit_amount
        return f"{self.transaction_date}: {amount} — {self.description[:50]}"


class ReconciliationSession(models.Model):
    """
    Tracks a bank reconciliation session — matching bank statements to system transactions.
    """

    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    bank_account = models.ForeignKey(
        BankAccount, on_delete=models.CASCADE, related_name='reconciliation_sessions'
    )
    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='reconciliation_sessions'
    )
    statement_start_date = models.DateField()
    statement_end_date = models.DateField()
    statement_closing_balance = models.DecimalField(
        max_digits=20, decimal_places=2
    )
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.IN_PROGRESS
    )
    matched_count = models.PositiveIntegerField(default=0)
    unmatched_count = models.PositiveIntegerField(default=0)
    difference = models.DecimalField(
        max_digits=20, decimal_places=2, default=Decimal('0.00'),
        help_text='Difference between bank balance and book balance'
    )
    reconciled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='reconciliation_sessions'
    )
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return (
            f"Reconciliation: {self.bank_account.bank_name} "
            f"({self.statement_start_date} to {self.statement_end_date})"
        )
