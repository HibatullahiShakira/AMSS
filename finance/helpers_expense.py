"""
Expense & Reminder Engine — Business Logic

Implements (from AMSS Architecture Section 6.2):
- Materiality scoring: obligation_amount / monthly_revenue
- Cash coverage ratio: current_cash / obligation_amount
- Urgency determination: CRITICAL / URGENT / NORMAL / LOW
- Smart reminder generation: scans obligations, creates intelligent reminders
- Expense anomaly detection: flags spikes vs historical norms
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum, Avg, StdDev
from django.utils import timezone


def get_monthly_revenue(business):
    """
    Estimate monthly revenue from the last 3 months of Income records.
    Falls back to annual_revenue / 12 if no transaction data exists.
    """
    from finance.models import Income

    three_months_ago = date.today() - timedelta(days=90)
    total_income = Income.objects.filter(
        business=business,
        date__gte=three_months_ago
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    if total_income > 0:
        return (total_income / Decimal('3')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Fallback to business annual_revenue field
    if business.annual_revenue and business.annual_revenue > 0:
        return (business.annual_revenue / Decimal('12')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    return Decimal('0.00')


def get_current_cash(business):
    """
    Estimate current cash from total Income minus total Expenses.
    In a production system this would read from the Chart of Accounts cash balance.
    """
    from finance.models import Income, Expense

    total_income = Income.objects.filter(
        business=business
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    total_expense = Expense.objects.filter(
        business=business
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return total_income - total_expense


def compute_materiality_score(obligation_amount, business):
    """
    Per Section 6.2 Step 1:
    materiality_score = obligation_amount / monthly_revenue
    High: > 0.20 (20%) | Medium: 0.05–0.20 | Low: < 0.05
    """
    monthly_revenue = get_monthly_revenue(business)
    if monthly_revenue <= 0:
        return Decimal('1.00')  # If no revenue, everything is high materiality

    score = (Decimal(str(obligation_amount)) / monthly_revenue).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    )
    return min(score, Decimal('99.9999'))


def compute_coverage_ratio(business, obligation_amount):
    """
    Per Section 6.2 Step 2:
    coverage_ratio = current_cash / obligation_amount
    """
    current_cash = get_current_cash(business)
    if obligation_amount <= 0:
        return Decimal('99.00')

    ratio = (current_cash / Decimal(str(obligation_amount))).quantize(
        Decimal('0.0001'), rounding=ROUND_HALF_UP
    )
    return ratio


def determine_urgency_level(materiality_score, coverage_ratio, days_until_due):
    """
    Per Section 6.2 Step 2–3:
    - CRITICAL: coverage < 1.0 (can't cover the obligation)
    - URGENT: coverage < 1.5 AND due within 14 days
    - NORMAL: medium materiality or due within 7 days
    - LOW: low materiality, well-covered, distant due date
    """
    materiality = float(materiality_score)
    coverage = float(coverage_ratio)

    if coverage < 1.0:
        return 'CRITICAL'
    if coverage < 1.5 and days_until_due <= 14:
        return 'URGENT'
    if materiality > 0.20 and days_until_due <= 21:
        return 'URGENT'
    if materiality > 0.05 or days_until_due <= 7:
        return 'NORMAL'
    return 'LOW'


def get_reminder_lead_days(urgency_level, materiality_score):
    """
    Per Section 6.2 Step 3:
    Returns the list of days-before-due to send reminders.
    """
    materiality = float(materiality_score)

    if urgency_level == 'CRITICAL':
        return [0]  # Immediate
    if materiality > 0.20:  # High materiality
        return [21, 14, 7, 3, 1]
    if materiality > 0.05:  # Medium materiality
        return [14, 7, 1]
    return [3]  # Low materiality


def generate_smart_reminders(business):
    """
    Scans all active recurring expenses and liabilities for the business.
    Creates or updates Reminder objects with computed intelligence scores.

    Returns a list of created/updated reminders.
    """
    from finance.models import Liability
    from finance.models_expense import RecurringExpense, Reminder, ReminderLog

    today = date.today()
    lookahead = today + timedelta(days=30)
    created_reminders = []

    # 1. Scan active recurring expenses
    recurring = RecurringExpense.objects.filter(
        business=business,
        status='ACTIVE',
        next_due_date__lte=lookahead
    )

    for rec in recurring:
        days_until = (rec.next_due_date - today).days
        materiality = compute_materiality_score(rec.amount, business)
        coverage = compute_coverage_ratio(business, rec.amount)
        urgency = determine_urgency_level(materiality, coverage, days_until)

        reminder, created = Reminder.objects.update_or_create(
            business=business,
            recurring_expense=rec,
            due_date=rec.next_due_date,
            defaults={
                'title': f"{rec.name} due",
                'description': f"{rec.name}: {rec.currency} {rec.amount} due on {rec.next_due_date}",
                'reminder_type': 'RECURRING_EXPENSE',
                'amount': rec.amount,
                'currency': rec.currency,
                'materiality_score': materiality,
                'coverage_ratio': coverage,
                'urgency_level': urgency,
                'user': rec.user,
            }
        )

        if created:
            ReminderLog.objects.create(
                reminder=reminder,
                action='CREATED',
                channel='IN_APP',
                message=f"Auto-generated reminder for {rec.name}"
            )

        created_reminders.append(reminder)

    # 2. Scan liabilities with upcoming due dates
    liabilities = Liability.objects.filter(
        business=business,
        due_date__lte=lookahead,
        due_date__gte=today
    )

    for liab in liabilities:
        outstanding = liab.get_outstanding_balance()
        if outstanding <= 0:
            continue

        days_until = (liab.due_date - today).days
        materiality = compute_materiality_score(outstanding, business)
        coverage = compute_coverage_ratio(business, outstanding)
        urgency = determine_urgency_level(materiality, coverage, days_until)

        reminder, created = Reminder.objects.update_or_create(
            business=business,
            liability=liab,
            due_date=liab.due_date,
            defaults={
                'title': f"{liab.name} payment due",
                'description': f"{liab.name}: ₦{outstanding} due on {liab.due_date}",
                'reminder_type': 'LIABILITY_PAYMENT',
                'amount': outstanding,
                'materiality_score': materiality,
                'coverage_ratio': coverage,
                'urgency_level': urgency,
            }
        )

        if created:
            ReminderLog.objects.create(
                reminder=reminder,
                action='CREATED',
                channel='IN_APP',
                message=f"Auto-generated reminder for liability: {liab.name}"
            )

        created_reminders.append(reminder)

    return created_reminders


def detect_expense_anomalies(business, lookback_months=3):
    """
    Detect anomalous expense spikes by comparing recent expenses
    against the business's historical norms per category.

    Uses simple z-score method: if current month spending in a category
    exceeds mean + 2*std_dev of historical spending, flag as anomaly.

    Returns list of anomaly dicts.
    """
    from finance.models import Expense

    today = date.today()
    current_month_start = today.replace(day=1)
    lookback_start = current_month_start - timedelta(days=lookback_months * 30)

    anomalies = []

    # Get all categories with expenses
    categories = Expense.objects.filter(
        business=business
    ).values_list('expense_category', flat=True).distinct()

    for category in categories:
        # Historical monthly averages (excluding current month)
        historical = Expense.objects.filter(
            business=business,
            expense_category=category,
            date__gte=lookback_start,
            date__lt=current_month_start
        ).aggregate(
            avg_amount=Avg('amount'),
            std_amount=StdDev('amount')
        )

        avg = historical['avg_amount'] or Decimal('0')
        std = historical['std_amount'] or Decimal('0')

        # Current month total for this category
        current_total = Expense.objects.filter(
            business=business,
            expense_category=category,
            date__gte=current_month_start
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        if avg > 0 and std > 0:
            z_score = float((current_total - avg) / std) if std > 0 else 0
            if z_score > 2.0:
                anomalies.append({
                    'category': category,
                    'current_month_total': float(current_total),
                    'historical_average': float(avg),
                    'historical_std_dev': float(std),
                    'z_score': round(z_score, 2),
                    'spike_percentage': round(
                        float((current_total - avg) / avg * 100), 1
                    ) if avg > 0 else 0,
                    'severity': 'HIGH' if z_score > 3.0 else 'MEDIUM',
                    'message': (
                        f"{category} spending is {round(float((current_total - avg) / avg * 100), 1)}% "
                        f"above average (₦{current_total:,.0f} vs avg ₦{avg:,.0f})"
                    )
                })

    return sorted(anomalies, key=lambda x: x['z_score'], reverse=True)


def get_expense_breakdown(business, start_date=None, end_date=None):
    """
    Returns expense breakdown by category for a given period.
    """
    from finance.models import Expense

    qs = Expense.objects.filter(business=business)
    if start_date:
        qs = qs.filter(date__gte=start_date)
    if end_date:
        qs = qs.filter(date__lte=end_date)

    breakdown = qs.values('expense_category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    grand_total = sum(item['total'] for item in breakdown)

    return {
        'breakdown': [
            {
                'category': item['expense_category'],
                'total': float(item['total']),
                'percentage': round(float(item['total'] / grand_total * 100), 1) if grand_total > 0 else 0
            }
            for item in breakdown
        ],
        'grand_total': float(grand_total),
        'period': {
            'start': str(start_date) if start_date else 'All time',
            'end': str(end_date) if end_date else 'Present'
        }
    }
