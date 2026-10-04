"""
Nigerian Tax Engine — Business Logic

Implements (from AMSS Architecture Section 8):
- VAT calculation (7.5%)
- WHT calculation based on service type
- Corporate Income Tax (CIT) computation
- Monthly VAT / Quarterly WHT / Annual CIT return generation
- FIRS deadline tracking
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum


def calculate_vat(amount, rate=Decimal('7.50')):
    """Calculate VAT amount based on base amount and rate."""
    return (Decimal(str(amount)) * (Decimal(str(rate)) / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


def calculate_wht(amount, service_type='CONTRACT'):
    """
    Calculate Withholding Tax based on Nigerian service types.
    Contract/Agency: 5%
    Professional/Management: 10%
    Rent/Dividend: 10%
    """
    rates = {
        'CONTRACT': Decimal('5.00'),
        'AGENCY': Decimal('5.00'),
        'PROFESSIONAL': Decimal('10.00'),
        'MANAGEMENT': Decimal('10.00'),
        'RENT': Decimal('10.00'),
        'DIVIDEND': Decimal('10.00'),
    }
    rate = rates.get(service_type.upper(), Decimal('5.00'))
    return (Decimal(str(amount)) * (rate / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )


def compute_cit_liability(business, fiscal_year):
    """
    Compute Corporate Income Tax liability for a given year.
    Small (< 25m NGN): 0%
    Medium (25m - 100m NGN): 20%
    Large (> 100m NGN): 30%
    """
    from finance.models import Income, Expense

    start_date = date(fiscal_year, 1, 1)
    end_date = date(fiscal_year, 12, 31)

    total_revenue = Income.objects.filter(
        business=business, date__year=fiscal_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    deductible_expenses = Expense.objects.filter(
        business=business, date__year=fiscal_year,
        expense_category__is_deductible=True
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    taxable_profit = max(total_revenue - deductible_expenses, Decimal('0.00'))

    # Determine rate based on revenue
    if total_revenue < Decimal('25000000'):
        rate = Decimal('0.00')
    elif total_revenue <= Decimal('100000000'):
        rate = Decimal('20.00')
    else:
        rate = Decimal('30.00')

    tax_liability = (taxable_profit * (rate / Decimal('100'))).quantize(
        Decimal('0.01'), rounding=ROUND_HALF_UP
    )

    return {
        'fiscal_year': fiscal_year,
        'total_revenue': float(total_revenue),
        'deductible_expenses': float(deductible_expenses),
        'taxable_profit': float(taxable_profit),
        'cit_rate': float(rate),
        'cit_liability': float(tax_liability)
    }


def generate_vat_return(business, month, year):
    """
    Generate a monthly VAT return summarizing output VAT (sales)
    and input VAT (purchases).
    """
    from finance.models_tax import TaxTransaction

    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    transactions = TaxTransaction.objects.filter(
        business=business,
        tax_type='VAT',
        date__gte=start_date,
        date__lte=end_date
    )

    # Note: In a full system we would distinguish between input and output VAT
    # For MVP, we assume all VAT transactions are output VAT (liability).
    total_vat = transactions.aggregate(total=Sum('tax_amount'))['total'] or Decimal('0.00')

    return {
        'period': f"{month:02d}-{year}",
        'start_date': str(start_date),
        'end_date': str(end_date),
        'total_vat_liability': float(total_vat),
        'transaction_count': transactions.count(),
    }


def get_filing_deadlines(business):
    """
    Returns upcoming FIRS tax filing deadlines.
    - VAT is due on the 21st of the following month.
    - WHT is due on the 21st of the following month.
    - CIT is due 6 months after the financial year end.
    """
    from finance.models_tax import TaxFilingDeadline

    today = date.today()
    deadlines = TaxFilingDeadline.objects.filter(
        business=business,
        is_filed=False,
        deadline_date__gte=today
    ).order_by('deadline_date')

    # If the system is fresh and has no deadlines populated, we would
    # typically auto-generate them here for the current month.
    # For now, we return what's in the DB.

    return [
        {
            'tax_type': d.tax_type,
            'period_name': d.period_name,
            'deadline_date': str(d.deadline_date),
            'days_remaining': (d.deadline_date - today).days,
            'is_filed': d.is_filed,
        }
        for d in deadlines
    ]
