"""
Analytics & Reporting Engine — Business Logic

Implements (from AMSS Architecture Section 9):
- P&L (Income Statement) generation
- Balance Sheet generation
- Cash Flow generation
- Financial KPIs (Current Ratio, DSCR, Burn Rate, Profit Margins)
"""

from datetime import date
from decimal import Decimal
from django.db.models import Sum


def get_date_range(period, start_date=None, end_date=None):
    """Resolve period string (e.g. 'MTD', 'YTD') into actual start/end dates."""
    today = date.today()
    if period == 'MTD':  # Month to date
        return today.replace(day=1), today
    elif period == 'YTD':  # Year to date
        return today.replace(month=1, day=1), today
    elif period == 'CUSTOM' and start_date and end_date:
        return start_date, end_date
    # Default to YTD
    return today.replace(month=1, day=1), today


def generate_profit_and_loss(business, start_date, end_date):
    """
    Generate P&L (Income Statement).
    Revenue - Expenses = Net Profit
    """
    from finance.models import Income, Expense

    # 1. Revenue
    revenues = Income.objects.filter(
        business=business, date__gte=start_date, date__lte=end_date
    ).values('source').annotate(total=Sum('amount'))
    
    total_revenue = sum(r['total'] for r in revenues) or Decimal('0.00')

    # 2. COGS / Direct Costs (Simplified for MVP, assuming specific categories)
    # For a full system, chart of accounts maps this directly.
    cogs_categories = ['Inventory', 'Raw Materials', 'Direct Labor']
    
    cogs_qs = Expense.objects.filter(
        business=business, date__gte=start_date, date__lte=end_date,
        expense_category__in=cogs_categories
    ).values('expense_category').annotate(total=Sum('amount'))
    
    total_cogs = sum(e['total'] for e in cogs_qs) or Decimal('0.00')
    gross_profit = total_revenue - total_cogs

    # 3. Operating Expenses (OPEX)
    opex_qs = Expense.objects.filter(
        business=business, date__gte=start_date, date__lte=end_date
    ).exclude(
        expense_category__in=cogs_categories
    ).values('expense_category').annotate(total=Sum('amount'))
    
    total_opex = sum(e['total'] for e in opex_qs) or Decimal('0.00')
    
    # 4. Net Profit
    net_profit = gross_profit - total_opex

    return {
        'period': f"{start_date} to {end_date}",
        'revenue': {
            'total': float(total_revenue),
            'breakdown': [{'category': r['source'], 'amount': float(r['total'])} for r in revenues]
        },
        'cogs': {
            'total': float(total_cogs),
            'breakdown': [{'category': e['expense_category'], 'amount': float(e['total'])} for e in cogs_qs]
        },
        'gross_profit': float(gross_profit),
        'gross_margin_pct': float(gross_profit / total_revenue * 100) if total_revenue > 0 else 0,
        'opex': {
            'total': float(total_opex),
            'breakdown': [{'category': e['expense_category'], 'amount': float(e['total'])} for e in opex_qs]
        },
        'net_profit': float(net_profit),
        'net_margin_pct': float(net_profit / total_revenue * 100) if total_revenue > 0 else 0,
    }


def generate_balance_sheet(business, as_of_date):
    """
    Generate Balance Sheet.
    Assets = Liabilities + Equity
    """
    from finance.models import Asset, Liability, Income, Expense

    # 1. Assets
    assets_qs = Asset.objects.filter(
        business=business, date_acquired__lte=as_of_date.year
    )
    
    # Simplified Cash calculation (All time Income - All time Expenses - Asset purchases)
    total_income = Income.objects.filter(
        business=business, date__lte=as_of_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_expense = Expense.objects.filter(
        business=business, date__lte=as_of_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    asset_spend = assets_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    cash_balance = total_income - total_expense - asset_spend
    
    # Other Assets (Current Value)
    fixed_assets_value = assets_qs.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
    
    total_assets = cash_balance + fixed_assets_value

    # 2. Liabilities
    liabilities_qs = Liability.objects.filter(
        business=business, date_incurred__lte=as_of_date
    )
    
    total_liabilities = sum(l.get_outstanding_balance() for l in liabilities_qs)
    
    # Current vs Long Term (simplified)
    # Short term = < 1 year to pay
    one_year_from_now = as_of_date.replace(year=as_of_date.year + 1)
    
    current_liabilities = sum(
        l.get_outstanding_balance() for l in liabilities_qs if l.due_date <= one_year_from_now
    )
    long_term_liabilities = total_liabilities - current_liabilities

    # 3. Equity (Calculated as Assets - Liabilities)
    total_equity = total_assets - total_liabilities

    return {
        'as_of_date': str(as_of_date),
        'assets': {
            'cash_and_equivalents': float(cash_balance),
            'fixed_assets': float(fixed_assets_value),
            'total': float(total_assets),
        },
        'liabilities': {
            'current': float(current_liabilities),
            'long_term': float(long_term_liabilities),
            'total': float(total_liabilities),
        },
        'equity': {
            'total': float(total_equity),
        },
        'check': {
            'is_balanced': float(total_assets) == float(total_liabilities + total_equity)
        }
    }


def generate_cash_flow(business, start_date, end_date):
    """
    Generate Cash Flow Statement (Direct Method for MVP).
    """
    from finance.models import Income, Expense, Asset, Liability

    # Operating Activities
    cash_in = Income.objects.filter(
        business=business, date__gte=start_date, date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    cash_out = Expense.objects.filter(
        business=business, date__gte=start_date, date__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    operating_cf = cash_in - cash_out

    # Investing Activities (Asset purchases)
    investing_cf = -(Asset.objects.filter(
        business=business, date_acquired__gte=start_date.year, date_acquired__lte=end_date.year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00'))

    # Financing Activities (New loans - Loan payments)
    # For MVP, assuming Liability principal amount is incoming cash if within period
    new_loans = Liability.objects.filter(
        business=business, date_incurred__gte=start_date, date_incurred__lte=end_date
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Simplification: we don't have a dedicated LoanPayment model yet, so we assume 0 outflow for now
    # A full implementation would track principal payments separately.
    loan_payments = Decimal('0.00') 
    
    financing_cf = new_loans - loan_payments

    net_change = operating_cf + investing_cf + financing_cf

    return {
        'period': f"{start_date} to {end_date}",
        'operating_activities': {
            'cash_received': float(cash_in),
            'cash_paid': float(cash_out),
            'net': float(operating_cf)
        },
        'investing_activities': {
            'net': float(investing_cf)
        },
        'financing_activities': {
            'new_loans': float(new_loans),
            'repayments': float(loan_payments),
            'net': float(financing_cf)
        },
        'net_change_in_cash': float(net_change)
    }


def calculate_kpis(business):
    """
    Calculate high-level financial KPIs for the dashboard.
    """
    today = date.today()
    ytd_start = today.replace(month=1, day=1)
    
    # Fetch P&L and Balance Sheet for KPI calcs
    pl = generate_profit_and_loss(business, ytd_start, today)
    bs = generate_balance_sheet(business, today)
    
    current_assets = bs['assets']['cash_and_equivalents'] # Simplified
    current_liabilities = bs['liabilities']['current']
    
    current_ratio = current_assets / current_liabilities if current_liabilities > 0 else 999.0
    
    # Burn Rate (Average monthly OPEX)
    months_passed = max(today.month, 1)
    monthly_burn_rate = pl['opex']['total'] / months_passed
    
    # Runway (Cash / Burn Rate)
    runway_months = current_assets / monthly_burn_rate if monthly_burn_rate > 0 else 999.0
    
    return {
        'profitability': {
            'gross_margin_pct': pl['gross_margin_pct'],
            'net_margin_pct': pl['net_margin_pct'],
            'ytd_revenue': pl['revenue']['total'],
            'ytd_profit': pl['net_profit'],
        },
        'liquidity': {
            'current_cash': bs['assets']['cash_and_equivalents'],
            'current_ratio': round(current_ratio, 2),
            'burn_rate_monthly': round(monthly_burn_rate, 2),
            'cash_runway_months': round(runway_months, 1) if runway_months != 999.0 else '99+'
        },
        'leverage': {
            'total_debt': bs['liabilities']['total'],
            'debt_to_equity': round(bs['liabilities']['total'] / bs['equity']['total'], 2) if bs['equity']['total'] > 0 else 0
        }
    }
