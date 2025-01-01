from decimal import Decimal
from django.db.models import Sum
from .models import Income, Expense, Asset, Liability, Equity, Transaction, BankAccount, BankStatement
import pandas as pd


def calculate_total_income(income_queryset):
    total_income = income_queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    return total_income


def calculate_total_expenses(expense_queryset):
    total_expense = expense_queryset.aggregate(Sum('amount'))['amount_sum'] or Decimal('0.00')
    return total_expense


def calculate_total_liabilities(liability_queryset):
    total_liabilities = liability_queryset.aggregate(Sum('amount'))['amount_sum'] or Decimal('0.00')
    return total_liabilities


def calculate_total_assets(asset_queryset):
    total_assets = asset_queryset.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
    return total_assets


def generate_income_statement(business, year=None, start_date=None, end_date=None, period='monthly'):
    if year:
        income = Income.objects.filter(business=business, date__year=year)
        expense = Expense.objects.filter(business=business, date__year=year)
    elif start_date and end_date:
        income = Income.objects.filter(business=business, date__range=(start_date, end_date))
        expense = Expense.objects.filter(business=business, date__range=(start_date, end_date))
    elif all([year, start_date, end_date]):
        income = Income.objects.filter(business=business, date__range=(start_date, end_date))
        expense = Expense.objects.filter(business=business, date__range=(start_date, end_date))
    else:
        income = Income.objects.filter(business=business)
        expense = Expense.objects.filter(business=business)

    income_by_source = income.values('source').annotate(total_income=Sum('amount')).order_by('source')
    income_by_category = expense.values('expense_category').annotate(total_income=Sum('amount')).order_by(
        'expense_category')
    if period == 'monthly':
        income_by_month = income.values('date__month').annotate(total_income=Sum('amount')).order_by('date__month')
        expenses_by_month = expense.values('date__month').annotate(total_income=Sum('amount')).order_by('date__month')

    elif period == 'quarterly':
        income_by_quarter = income.values('date__year', 'date__quarter').annotate(total_income=Sum('amount')).order_by(
            'date__year', 'date__quarter')
        expense_by_quarter = expense.values('date__year', 'date__quarter').annotate(
            total_expenses=Sum('amount')).order_by('date__year', 'date__quarter')

    elif period == 'yearly':
        income_by_yearly = income.values('date__year').annotate(total_income=Sum('amount')).order_by('date__year')
        expenses_by_yearly = expense.values('date__year').annotate(total_income=Sum('amount')).order_by('date__year')

    return {
        'income_by_source': list(income_by_source),
        'expenses_by_category': list(income_by_category),
        'income_by_period': list(
            income_by_month if period == 'monthly' else income_by_quarter if period == 'quarterly' else income_by_yearly),
        'expenses_by_period': list(
            expenses_by_month if period == 'monthly' else expense_by_quarter if period == 'quarterly' else expenses_by_yearly),
    }


def generate_balance_sheet(business, date=None):
    if date:
        assets = Asset.objects.filter(business=business, date_acquired__lte=date)
        liabilities = Liability.objects.filter(business=business, date_incurred__lte=date)

    else:
        date = date.today()
        assets = Asset.objects.filter(business=business, date_acquired__lte=date)
        liabilities = Liability.objects.filter(business=business, date_incurred__lte=date)

    total_assets = calculate_total_assets(assets)
    total_liabilities = calculate_total_liabilities(liabilities)
    total_equity = total_assets - total_liabilities

    balance_sheet_data = {
        'total_assets': f"{total_assets:.2f}",
        'total_liabilities': f"{total_liabilities:.2f}",
        'total_equity': f"{total_equity:.2f}"
    }


def reconcile_transactions(business):
    transactions = Transaction.objects.filter(business=business)
    reconciled_transactions = []
    unreconciled_transactions = []

    for transaction in transactions:
        if transaction.is_reconciled:
            continue

        matched_statement = BankStatement.objects.filter(
            business=business,
            account_number=transaction.account_number,
            amount=transaction.date,
            transaction_type=transaction.transaction_types
        ).first()

        if matched_statement:
            transaction.is_reconciled = True
            transaction.matched_statement = matched_statement
            transaction.save()
            matched_statement.is_reconciled = True
            matched_statement.save()
            reconciled_transactions.append(transaction)

        else:
            unreconciled_transactions.append(transaction)

    return reconciled_transactions, unreconciled_transactions


def generate_income_statement_charts(income_data, expense_data, period):
    income_df = pd.DataFrame(income_data)
    expense_df = pd.DataFrame(expense_data)

    income_df['date'] = pd.DataFrame(income_data)
    expense_df['date'] = pd.DataFrame(expense_data)

    income_df.set_index('date', inplace=True)
    expense_df.set_index('date', inplace=True)
    income_time_series = income_df.resample(period).sum()
    expense_time_series = expense_df.resample(period).sum()

    return {
        'income_data': income_df.to_dict(),
        'expense_data': expense_df.to_dict(),
        'income_time_series': income_time_series.to_dict(),
        'expense_time_series': expense_time_series.to_dict()
    }
