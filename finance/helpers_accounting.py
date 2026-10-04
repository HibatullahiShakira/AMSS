"""
Core Accounting Business Logic

Implements:
- Default Chart of Accounts seeding for Nigerian businesses
- Journal entry creation helpers (auto-create from Income/Expense)
- Financial report generators: Trial Balance, Income Statement, Balance Sheet, Cash Flow
- Bank reconciliation auto-matching algorithm
"""

from datetime import date
from decimal import Decimal

from django.db import transaction as db_transaction
from django.db.models import Sum, Q, F
from django.utils import timezone

from .models import Income, Expense
from .models_accounting import (
    Account, AccountType, JournalEntry, JournalEntryLine,
    Transaction, BankAccount, BankStatement, ReconciliationSession,
)


# ─────────────────────────────────────────────────────────────────────
# DEFAULT CHART OF ACCOUNTS — Nigerian SME Standard
# ─────────────────────────────────────────────────────────────────────

DEFAULT_ACCOUNTS = [
    # Assets (1xxx)
    {'code': '1000', 'name': 'Cash and Cash Equivalents', 'type': AccountType.ASSET, 'system': True},
    {'code': '1010', 'name': 'Bank — Primary Account', 'type': AccountType.ASSET, 'system': True},
    {'code': '1020', 'name': 'Bank — Savings Account', 'type': AccountType.ASSET, 'system': False},
    {'code': '1100', 'name': 'Accounts Receivable', 'type': AccountType.ASSET, 'system': True},
    {'code': '1200', 'name': 'Inventory', 'type': AccountType.ASSET, 'system': False},
    {'code': '1300', 'name': 'Prepaid Expenses', 'type': AccountType.ASSET, 'system': False},
    {'code': '1500', 'name': 'Property, Plant & Equipment', 'type': AccountType.ASSET, 'system': True},
    {'code': '1510', 'name': 'Vehicles', 'type': AccountType.ASSET, 'system': False},
    {'code': '1520', 'name': 'Machinery & Equipment', 'type': AccountType.ASSET, 'system': False},
    {'code': '1530', 'name': 'Furniture & Fittings', 'type': AccountType.ASSET, 'system': False},
    {'code': '1540', 'name': 'IT Equipment', 'type': AccountType.ASSET, 'system': False},
    {'code': '1550', 'name': 'Generator & Power', 'type': AccountType.ASSET, 'system': False},
    {'code': '1600', 'name': 'Accumulated Depreciation', 'type': AccountType.ASSET, 'system': True},
    {'code': '1700', 'name': 'Intangible Assets', 'type': AccountType.ASSET, 'system': False},

    # Liabilities (2xxx)
    {'code': '2000', 'name': 'Accounts Payable', 'type': AccountType.LIABILITY, 'system': True},
    {'code': '2100', 'name': 'Short-term Loans', 'type': AccountType.LIABILITY, 'system': False},
    {'code': '2200', 'name': 'Accrued Expenses', 'type': AccountType.LIABILITY, 'system': False},
    {'code': '2300', 'name': 'VAT Payable', 'type': AccountType.LIABILITY, 'system': True},
    {'code': '2310', 'name': 'WHT Payable', 'type': AccountType.LIABILITY, 'system': True},
    {'code': '2320', 'name': 'PAYE Payable', 'type': AccountType.LIABILITY, 'system': False},
    {'code': '2400', 'name': 'Long-term Loans', 'type': AccountType.LIABILITY, 'system': False},
    {'code': '2500', 'name': 'Equipment Finance Payable', 'type': AccountType.LIABILITY, 'system': False},

    # Equity (3xxx)
    {'code': '3000', 'name': "Owner's Capital", 'type': AccountType.EQUITY, 'system': True},
    {'code': '3100', 'name': "Owner's Drawings", 'type': AccountType.EQUITY, 'system': False},
    {'code': '3200', 'name': 'Retained Earnings', 'type': AccountType.EQUITY, 'system': True},

    # Revenue (4xxx)
    {'code': '4000', 'name': 'Sales Revenue', 'type': AccountType.REVENUE, 'system': True},
    {'code': '4100', 'name': 'Service Revenue', 'type': AccountType.REVENUE, 'system': False},
    {'code': '4200', 'name': 'Investment Income', 'type': AccountType.REVENUE, 'system': False},
    {'code': '4300', 'name': 'Other Income', 'type': AccountType.REVENUE, 'system': False},
    {'code': '4400', 'name': 'Loan Income', 'type': AccountType.REVENUE, 'system': False},

    # Expenses (5xxx)
    {'code': '5000', 'name': 'Cost of Goods Sold', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5100', 'name': 'Rent Expense', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5200', 'name': 'Utilities Expense', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5300', 'name': 'Salaries & Wages', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5400', 'name': 'Office Supplies', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5500', 'name': 'Travel & Transportation', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5600', 'name': 'Marketing & Advertising', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5700', 'name': 'Maintenance & Repairs', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5800', 'name': 'Depreciation Expense', 'type': AccountType.EXPENSE, 'system': True},
    {'code': '5900', 'name': 'Bank Charges', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5910', 'name': 'Interest Expense', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5920', 'name': 'Insurance Expense', 'type': AccountType.EXPENSE, 'system': False},
    {'code': '5999', 'name': 'Miscellaneous Expense', 'type': AccountType.EXPENSE, 'system': False},
]


def seed_default_accounts(business):
    """
    Create the default chart of accounts for a newly registered business.
    Idempotent — skips accounts that already exist.
    """
    created_count = 0
    for acct_data in DEFAULT_ACCOUNTS:
        _, created = Account.objects.get_or_create(
            business=business,
            code=acct_data['code'],
            defaults={
                'name': acct_data['name'],
                'account_type': acct_data['type'],
                'is_system_account': acct_data['system'],
            }
        )
        if created:
            created_count += 1
    return created_count


# ─────────────────────────────────────────────────────────────────────
# INCOME / EXPENSE → JOURNAL ENTRY AUTO-CREATION
# Maps the existing single-entry Income/Expense to double-entry journals
# ─────────────────────────────────────────────────────────────────────

# Mapping from Income source choices → revenue account codes
INCOME_SOURCE_TO_ACCOUNT = {
    'Sales': '4000',       # Sales Revenue
    'Investment': '4200',  # Investment Income
    'Loan': '4400',        # Loan Income
    'Other': '4300',       # Other Income
}

# Mapping from Expense category choices → expense account codes
EXPENSE_CATEGORY_TO_ACCOUNT = {
    'Rent': '5100',
    'Utilities': '5200',
    'Salaries': '5300',
    'Office Supplies': '5400',
    'Travel': '5500',
    'Marketing': '5600',
    'Maintenance': '5700',
    'Miscellaneous': '5999',
}


def create_journal_entry_from_income(income_instance):
    """
    Auto-create a double-entry journal when an Income record is saved.

    Debit:  Cash / Bank (Asset ↑)
    Credit: Revenue account (Revenue ↑)
    """
    business = income_instance.business
    revenue_code = INCOME_SOURCE_TO_ACCOUNT.get(income_instance.source, '4300')

    try:
        cash_account = Account.objects.get(business=business, code='1000')
        revenue_account = Account.objects.get(business=business, code=revenue_code)
    except Account.DoesNotExist:
        # Chart of accounts not yet seeded — skip
        return None

    with db_transaction.atomic():
        journal = JournalEntry.objects.create(
            business=business,
            date=income_instance.date.date() if hasattr(income_instance.date, 'date') else income_instance.date,
            description=f"Income: {income_instance.description}",
            status=JournalEntry.Status.POSTED,
            entry_type=JournalEntry.EntryType.AUTO_GENERATED,
            created_by=income_instance.user,
            posted_by=income_instance.user,
            posted_at=timezone.now(),
            source_module='finance',
        )

        # Debit Cash
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=cash_account,
            debit_amount=income_instance.amount,
            credit_amount=Decimal('0.00'),
            description=f"Cash received: {income_instance.description}",
        )

        # Credit Revenue
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=income_instance.amount,
            description=f"Revenue: {income_instance.source} — {income_instance.description}",
        )

        # Create transaction record
        Transaction.objects.create(
            business=business,
            journal_entry=journal,
            transaction_type=Transaction.TransactionType.INCOME,
            amount=income_instance.amount,
            currency=income_instance.currency,
            date=journal.date,
            description=income_instance.description,
            user=income_instance.user,
        )

    return journal


def create_journal_entry_from_expense(expense_instance):
    """
    Auto-create a double-entry journal when an Expense record is saved.

    Debit:  Expense account (Expense ↑)
    Credit: Cash / Bank (Asset ↓)
    """
    business = expense_instance.business
    expense_code = EXPENSE_CATEGORY_TO_ACCOUNT.get(
        expense_instance.expense_category, '5999'
    )

    try:
        cash_account = Account.objects.get(business=business, code='1000')
        expense_account = Account.objects.get(business=business, code=expense_code)
    except Account.DoesNotExist:
        return None

    with db_transaction.atomic():
        journal = JournalEntry.objects.create(
            business=business,
            date=expense_instance.date.date() if hasattr(expense_instance.date, 'date') else expense_instance.date,
            description=f"Expense: {expense_instance.description}",
            status=JournalEntry.Status.POSTED,
            entry_type=JournalEntry.EntryType.AUTO_GENERATED,
            created_by=expense_instance.user,
            posted_by=expense_instance.user,
            posted_at=timezone.now(),
            source_module='finance',
        )

        # Debit Expense
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=expense_account,
            debit_amount=expense_instance.amount,
            credit_amount=Decimal('0.00'),
            description=f"{expense_instance.expense_category}: {expense_instance.description}",
        )

        # Credit Cash
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=cash_account,
            debit_amount=Decimal('0.00'),
            credit_amount=expense_instance.amount,
            description=f"Cash paid: {expense_instance.description}",
        )

        Transaction.objects.create(
            business=business,
            journal_entry=journal,
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=expense_instance.amount,
            currency=expense_instance.currency,
            date=journal.date,
            description=expense_instance.description,
            user=expense_instance.user,
        )

    return journal


# ─────────────────────────────────────────────────────────────────────
# FINANCIAL REPORTS
# ─────────────────────────────────────────────────────────────────────

def generate_trial_balance(business, as_of_date=None):
    """
    Generate a Trial Balance — list of all accounts with their debit/credit balances.
    The total of all debits must equal the total of all credits.

    Returns a dict with:
    - accounts: list of {code, name, type, debit_balance, credit_balance}
    - total_debits: sum
    - total_credits: sum
    - is_balanced: bool
    """
    if as_of_date is None:
        as_of_date = date.today()

    accounts = Account.objects.filter(
        business=business, is_active=True
    ).order_by('code')

    trial_balance = []
    total_debits = Decimal('0.00')
    total_credits = Decimal('0.00')

    for account in accounts:
        totals = account.journal_lines.filter(
            journal_entry__status=JournalEntry.Status.POSTED,
            journal_entry__date__lte=as_of_date,
        ).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount'),
        )

        debit_total = totals['total_debit'] or Decimal('0.00')
        credit_total = totals['total_credit'] or Decimal('0.00')

        # Net balance
        net = debit_total - credit_total

        entry = {
            'account_id': account.id,
            'code': account.code,
            'name': account.name,
            'account_type': account.account_type,
            'debit_balance': net if net > 0 else Decimal('0.00'),
            'credit_balance': abs(net) if net < 0 else Decimal('0.00'),
        }

        if net > 0:
            total_debits += net
        else:
            total_credits += abs(net)

        # Only include accounts with activity
        if debit_total > 0 or credit_total > 0:
            trial_balance.append(entry)

    return {
        'as_of_date': str(as_of_date),
        'accounts': trial_balance,
        'total_debits': total_debits,
        'total_credits': total_credits,
        'is_balanced': total_debits == total_credits,
    }


def generate_income_statement(business, start_date, end_date):
    """
    Generate an Income Statement (Profit & Loss) for a date range.

    Revenue - Expenses = Net Income (or Net Loss)

    Returns:
    - revenue_items: list of {code, name, amount}
    - expense_items: list of {code, name, amount}
    - total_revenue, total_expenses, net_income
    """
    revenue_accounts = Account.objects.filter(
        business=business,
        account_type=AccountType.REVENUE,
        is_active=True,
    )

    expense_accounts = Account.objects.filter(
        business=business,
        account_type=AccountType.EXPENSE,
        is_active=True,
    )

    def get_account_balances(accounts, start, end):
        items = []
        total = Decimal('0.00')
        for account in accounts:
            totals = account.journal_lines.filter(
                journal_entry__status=JournalEntry.Status.POSTED,
                journal_entry__date__gte=start,
                journal_entry__date__lte=end,
            ).aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount'),
            )
            debit = totals['total_debit'] or Decimal('0.00')
            credit = totals['total_credit'] or Decimal('0.00')

            # Revenue: credit-normal, Expense: debit-normal
            if account.account_type == AccountType.REVENUE:
                amount = credit - debit
            else:
                amount = debit - credit

            if amount != 0:
                items.append({
                    'account_id': account.id,
                    'code': account.code,
                    'name': account.name,
                    'amount': amount,
                })
                total += amount

        return items, total

    revenue_items, total_revenue = get_account_balances(
        revenue_accounts, start_date, end_date
    )
    expense_items, total_expenses = get_account_balances(
        expense_accounts, start_date, end_date
    )

    net_income = total_revenue - total_expenses

    return {
        'period': f"{start_date} to {end_date}",
        'revenue': {
            'items': revenue_items,
            'total': total_revenue,
        },
        'expenses': {
            'items': expense_items,
            'total': total_expenses,
        },
        'net_income': net_income,
        'is_profitable': net_income > 0,
    }


def generate_balance_sheet(business, as_of_date=None):
    """
    Generate a Balance Sheet — Assets = Liabilities + Equity.

    Returns:
    - assets: {items, total}
    - liabilities: {items, total}
    - equity: {items, total}
    - is_balanced: bool (assets == liabilities + equity)
    """
    if as_of_date is None:
        as_of_date = date.today()

    def get_balances_by_type(account_type):
        accounts = Account.objects.filter(
            business=business,
            account_type=account_type,
            is_active=True,
        )
        items = []
        total = Decimal('0.00')

        for account in accounts:
            totals = account.journal_lines.filter(
                journal_entry__status=JournalEntry.Status.POSTED,
                journal_entry__date__lte=as_of_date,
            ).aggregate(
                total_debit=Sum('debit_amount'),
                total_credit=Sum('credit_amount'),
            )
            debit = totals['total_debit'] or Decimal('0.00')
            credit = totals['total_credit'] or Decimal('0.00')

            if account_type in [AccountType.ASSET, AccountType.EXPENSE]:
                balance = debit - credit
            else:
                balance = credit - debit

            if balance != 0:
                items.append({
                    'account_id': account.id,
                    'code': account.code,
                    'name': account.name,
                    'balance': balance,
                })
                total += balance

        return items, total

    asset_items, total_assets = get_balances_by_type(AccountType.ASSET)
    liability_items, total_liabilities = get_balances_by_type(AccountType.LIABILITY)
    equity_items, total_equity = get_balances_by_type(AccountType.EQUITY)

    # Add net income to retained earnings for equity
    # (Revenue - Expenses for current period)
    revenue_accounts = Account.objects.filter(
        business=business, account_type=AccountType.REVENUE
    )
    expense_accounts = Account.objects.filter(
        business=business, account_type=AccountType.EXPENSE
    )

    total_revenue = Decimal('0.00')
    for account in revenue_accounts:
        totals = account.journal_lines.filter(
            journal_entry__status=JournalEntry.Status.POSTED,
            journal_entry__date__lte=as_of_date,
        ).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount'),
        )
        total_revenue += (totals['total_credit'] or Decimal('0.00')) - (totals['total_debit'] or Decimal('0.00'))

    total_expenses_val = Decimal('0.00')
    for account in expense_accounts:
        totals = account.journal_lines.filter(
            journal_entry__status=JournalEntry.Status.POSTED,
            journal_entry__date__lte=as_of_date,
        ).aggregate(
            total_debit=Sum('debit_amount'),
            total_credit=Sum('credit_amount'),
        )
        total_expenses_val += (totals['total_debit'] or Decimal('0.00')) - (totals['total_credit'] or Decimal('0.00'))

    net_income = total_revenue - total_expenses_val
    total_equity += net_income

    if net_income != 0:
        equity_items.append({
            'account_id': None,
            'code': 'NET',
            'name': 'Net Income (Current Period)',
            'balance': net_income,
        })

    return {
        'as_of_date': str(as_of_date),
        'assets': {
            'items': asset_items,
            'total': total_assets,
        },
        'liabilities': {
            'items': liability_items,
            'total': total_liabilities,
        },
        'equity': {
            'items': equity_items,
            'total': total_equity,
        },
        'is_balanced': total_assets == (total_liabilities + total_equity),
    }


def generate_cash_flow_statement(business, start_date, end_date):
    """
    Generate a Cash Flow Statement using the direct method.

    Categorises all cash movements into:
    - Operating Activities (income, expenses)
    - Investing Activities (asset purchases/disposals)
    - Financing Activities (loans, equity)
    """
    transactions = Transaction.objects.filter(
        business=business,
        date__gte=start_date,
        date__lte=end_date,
    )

    operating_types = [
        Transaction.TransactionType.INCOME,
        Transaction.TransactionType.EXPENSE,
    ]
    investing_types = [
        Transaction.TransactionType.ASSET_PURCHASE,
        Transaction.TransactionType.ASSET_DISPOSAL,
    ]
    financing_types = [
        Transaction.TransactionType.LOAN_DISBURSEMENT,
        Transaction.TransactionType.LOAN_REPAYMENT,
    ]

    def aggregate_by_types(types):
        inflows = transactions.filter(
            transaction_type__in=types,
        ).filter(
            Q(transaction_type=Transaction.TransactionType.INCOME) |
            Q(transaction_type=Transaction.TransactionType.ASSET_DISPOSAL) |
            Q(transaction_type=Transaction.TransactionType.LOAN_DISBURSEMENT)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        outflows = transactions.filter(
            transaction_type__in=types,
        ).filter(
            Q(transaction_type=Transaction.TransactionType.EXPENSE) |
            Q(transaction_type=Transaction.TransactionType.ASSET_PURCHASE) |
            Q(transaction_type=Transaction.TransactionType.LOAN_REPAYMENT) |
            Q(transaction_type=Transaction.TransactionType.TAX_PAYMENT)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        return inflows, outflows

    op_in, op_out = aggregate_by_types(operating_types)
    inv_in, inv_out = aggregate_by_types(investing_types)
    fin_in, fin_out = aggregate_by_types(financing_types)

    net_operating = op_in - op_out
    net_investing = inv_in - inv_out
    net_financing = fin_in - fin_out
    net_change = net_operating + net_investing + net_financing

    return {
        'period': f"{start_date} to {end_date}",
        'operating_activities': {
            'inflows': op_in,
            'outflows': op_out,
            'net': net_operating,
        },
        'investing_activities': {
            'inflows': inv_in,
            'outflows': inv_out,
            'net': net_investing,
        },
        'financing_activities': {
            'inflows': fin_in,
            'outflows': fin_out,
            'net': net_financing,
        },
        'net_change_in_cash': net_change,
    }


# ─────────────────────────────────────────────────────────────────────
# BANK RECONCILIATION ENGINE
# ─────────────────────────────────────────────────────────────────────

def auto_reconcile_transactions(reconciliation_session):
    """
    Automated bank reconciliation matching algorithm.

    Strategy (in order of confidence):
    1. Exact match: same amount + same date + same reference
    2. Amount + date match: same amount within ±2 days
    3. Amount match: same amount, any date within statement range

    Each matched pair is linked and flagged as reconciled.
    Returns match statistics.
    """
    bank_account = reconciliation_session.bank_account
    business = reconciliation_session.business
    start = reconciliation_session.statement_start_date
    end = reconciliation_session.statement_end_date

    unmatched_statements = BankStatement.objects.filter(
        bank_account=bank_account,
        transaction_date__gte=start,
        transaction_date__lte=end,
        is_reconciled=False,
    )

    unmatched_transactions = Transaction.objects.filter(
        business=business,
        date__gte=start,
        date__lte=end,
        is_reconciled=False,
    )

    matched = 0
    unmatched = 0

    for statement in unmatched_statements:
        stmt_amount = statement.credit_amount - statement.debit_amount

        # Strategy 1: Exact match (amount + date + reference)
        match = unmatched_transactions.filter(
            amount=abs(stmt_amount),
            date=statement.transaction_date,
            external_reference=statement.reference,
            is_reconciled=False,
        ).first()

        # Strategy 2: Amount + date (±2 days)
        if not match:
            from datetime import timedelta
            match = unmatched_transactions.filter(
                amount=abs(stmt_amount),
                date__gte=statement.transaction_date - timedelta(days=2),
                date__lte=statement.transaction_date + timedelta(days=2),
                is_reconciled=False,
            ).first()

        # Strategy 3: Amount only (within statement range)
        if not match:
            match = unmatched_transactions.filter(
                amount=abs(stmt_amount),
                is_reconciled=False,
            ).first()

        if match:
            statement.is_reconciled = True
            statement.matched_transaction = match
            statement.save()

            match.is_reconciled = True
            match.save()

            matched += 1
        else:
            unmatched += 1

    reconciliation_session.matched_count = matched
    reconciliation_session.unmatched_count = unmatched
    reconciliation_session.save()

    return {'matched': matched, 'unmatched': unmatched}


def create_journal_entry_from_invoice(invoice_instance):
    """
    Auto-create a double-entry journal when an Invoice is sent/created.
    Debit: Accounts Receivable (1200)
    Credit: Sales Revenue (4100)
    """
    business = invoice_instance.business
    try:
        ar_account = Account.objects.get(business=business, code='1200')
        revenue_account = Account.objects.get(business=business, code='4100')
    except Account.DoesNotExist:
        return None

    if invoice_instance.total_amount <= 0:
        return None

    with db_transaction.atomic():
        journal = JournalEntry.objects.create(
            business=business,
            date=invoice_instance.issue_date,
            description=f"Invoice #{invoice_instance.invoice_number} Issued",
            status=JournalEntry.Status.POSTED,
            entry_type=JournalEntry.EntryType.AUTO_GENERATED,
            created_by=invoice_instance.created_by,
            posted_by=invoice_instance.created_by,
            posted_at=timezone.now(),
            source_module='billing',
        )

        # Debit AR
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=ar_account,
            debit_amount=invoice_instance.total_amount,
            credit_amount=Decimal('0.00'),
            description=f"AR for Invoice #{invoice_instance.invoice_number}",
        )

        # Credit Revenue
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=revenue_account,
            debit_amount=Decimal('0.00'),
            credit_amount=invoice_instance.total_amount,
            description=f"Revenue for Invoice #{invoice_instance.invoice_number}",
        )
        return journal


def create_journal_entry_from_payment(payment_instance):
    """
    Auto-create a double-entry journal when a Payment is received.
    Debit: Cash/Bank (1000)
    Credit: Accounts Receivable (1200)
    """
    business = payment_instance.business
    try:
        cash_account = Account.objects.get(business=business, code='1000')
        ar_account = Account.objects.get(business=business, code='1200')
    except Account.DoesNotExist:
        return None

    if payment_instance.amount <= 0:
        return None

    with db_transaction.atomic():
        journal = JournalEntry.objects.create(
            business=business,
            date=payment_instance.payment_date,
            description=f"Payment received for Invoice #{payment_instance.invoice.invoice_number}",
            status=JournalEntry.Status.POSTED,
            entry_type=JournalEntry.EntryType.AUTO_GENERATED,
            created_by=payment_instance.received_by,
            posted_by=payment_instance.received_by,
            posted_at=timezone.now(),
            source_module='billing',
        )

        # Debit Cash
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=cash_account,
            debit_amount=payment_instance.amount,
            credit_amount=Decimal('0.00'),
            description=f"Cash from Payment on Invoice #{payment_instance.invoice.invoice_number}",
        )

        # Credit AR
        JournalEntryLine.objects.create(
            journal_entry=journal,
            account=ar_account,
            debit_amount=Decimal('0.00'),
            credit_amount=payment_instance.amount,
            description=f"AR Reduced by Payment on Invoice #{payment_instance.invoice.invoice_number}",
        )

        return journal
