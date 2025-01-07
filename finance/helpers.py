from datetime import date
from decimal import Decimal
from random import random
from django.db.models import Sum
import numpy as np
from datetime import date


def calculate_remaining_useful_life_years(asset):
    current_year = date.today().year
    years_used = current_year - asset.date_acquired
    remaining_years = asset.useful_life - years_used
    return max(remaining_years, 0)


def calculate_remaining_useful_life_months(asset):
    remaining_years = calculate_remaining_useful_life_years(asset)
    return remaining_years * 12


def calculate_remaining_residual_value(asset):
    if asset.is_appreciating:
        return float(asset.current_value)
    else:
        remaining_life_years = calculate_remaining_useful_life_years(asset)
        depreciation_per_year = (float(asset.amount) - float(asset.residual_value)) / asset.useful_life
        remaining_value = max(
            float(asset.amount) - (depreciation_per_year * (asset.useful_life - remaining_life_years)),
            float(asset.residual_value))
        return remaining_value


def generate_depreciation_warning(asset):
    warnings = []
    remaining_useful_life_years = calculate_remaining_useful_life_years(asset)
    if remaining_useful_life_years < 2:
        warnings.append("The asset is nearing the end of its useful life.")
    if float(asset.current_value) < float(asset.residual_value) * 1.1:
        warnings.append("The asset's value is close to its residual value.")
    return warnings


def get_valuation_method_explanation(method):
    explanations = {
        'Straight-Line': 'Straight-Line depreciation reduces the asset’s value by an equal amount each year over its '
                         'useful life.',
        'Declining-Balance': 'Declining-Balance depreciation reduces the asset’s value by a fixed percentage each year.',
        'Units-of-Production': 'Units-of-Production depreciation is based on the actual usage of the asset.',
        'Sum-of-the-Years-Digits': 'Sum-of-the-Years-Digits depreciation is higher in the earlier years and decreases '
                                   'over time.',
        'Double-Declining-Balance': 'Double-Declining-Balance is an accelerated depreciation method that results in '
                                    'higher depreciation in the early years.',
        'Appreciation': 'Appreciation increases the asset’s value over time, usually by a fixed percentage.'
    }
    return explanations.get(method, 'No explanation available for this valuation method.')


def generate_asset_project_simulations(asset, num_simulations=1000, risk_tolerance="moderate"):
    annual_maintenance_cost = float(asset.annual_maintenance_cost)
    residual_value = float(asset.residual_value)
    is_appreciating = asset.is_appreciating
    appreciation_rate = float(asset.appreciation_rate) / 100
    depreciation_rate = float(asset.depreciation_rate) / 100

    historical_rates = []
    for year in range(1, 6):
        if is_appreciating:
            rate = np.random.normal(appreciation_rate, appreciation_rate * 0.1)
        else:
            rate = np.random.normal(depreciation_rate, depreciation_rate * 0.1)
        historical_rates.append(rate)
    market_volatility = np.std(historical_rates)

    future_values_all_years = []

    for year in range(1, 6):
        future_values_year = []
        for _ in range(num_simulations):
            market_fluctuation = np.random.normal(loc=0, scale=market_volatility)
            if is_appreciating:
                future_value = float(asset.amount) * (1 + appreciation_rate + market_fluctuation) ** year
            else:
                future_value = max(float(asset.amount) * (1 - depreciation_rate + market_fluctuation) ** year,
                                   residual_value)
            future_value -= annual_maintenance_cost * year
            future_values_year.append(float(future_value))

        future_values_all_years.append(future_values_year)

    mean_future_values = [np.mean(values) for values in future_values_all_years]
    std_dev_future_values = [np.std(values) for values in future_values_all_years]
    percentile_5 = [np.percentile(values, 5) for values in future_values_all_years]
    percentile_25 = [np.percentile(values, 25) for values in future_values_all_years]
    percentile_75 = [np.percentile(values, 75) for values in future_values_all_years]
    percentile_95 = [np.percentile(values, 95) for values in future_values_all_years]

    scenarios = []
    for year in range(5):
        scenario = {
            'year': year + 1,
            'mean_value': round(mean_future_values[year], 2),  # Round to 2 decimal places
            'std_dev': round(std_dev_future_values[year], 2),
            'percentile_25': round(percentile_25[year], 2),
            'percentile_75': round(percentile_75[year], 2),
            'percentile_5': round(percentile_5[year], 2),
            'percentile_95': round(percentile_95[year], 2),
            'best_case': round(percentile_95[year], 2),
            'worst_case': round(percentile_5[year], 2),
            'most_likely': round(mean_future_values[year], 2),
            'story': ''
        }

        if is_appreciating:
            if risk_tolerance == "low":
                scenario[
                    'story'] = (f"In the best-case scenario, the asset's value could appreciate significantly, "
                                f"potentially reaching ${scenario['best_case']} in year {year + 1}. However, "
                                f"for those who are risk-averse, the value could also drop below $"
                                f"{scenario['worst_case']}.")
            elif risk_tolerance == "high":
                scenario[
                    'story'] = (f"If you're feeling adventurous, there's potential for significant gains! The asset's "
                                f"value could reach as high as ${scenario['best_case']} in year {year + 1}. But be "
                                f"cautious, as it could also dip to ${scenario['worst_case']}.")
            else:  # Default to moderate
                scenario[
                    'story'] = f"Over the next few years, you can expect the asset's value to be around ${scenario['mean_value']} in year {year + 1}. There's room for variation, with possible values ranging from ${scenario['percentile_25']} to ${scenario['percentile_75']}."

        else:
            warnings = generate_depreciation_warning(asset)
            if warnings:
                scenario[
                    'story'] = (f"In {year + 1} years, the asset may depreciate, and here are some things to watch out "
                                f"for: {', '.join(warnings)}. Keep in mind that the most likely value could"
                                f" be around ${scenario['most_likely']}.")

        scenarios.append(scenario)

    return scenarios


def get_comprehensive_breakdown(asset):
    detailed_info = {
        'name': asset.name,
        'description': asset.description,
        'amount': asset.amount,
        'date_acquired': asset.date_acquired,
        'asset_types': asset.asset_types,
        'depreciation_rate': asset.depreciation_rate,
        'appreciation_rate': asset.appreciation_rate,
        'current_value': asset.current_value,
        'useful_life': asset.useful_life,
        'residual_value': asset.residual_value,
        'valuation_method': asset.valuation_method,
        'is_appreciating': asset.is_appreciating,
        'monthly_depreciation_rate': asset.yearly_depreciation_rate / 12,
        'yearly_depreciation_rate': asset.yearly_depreciation_rate,
        'monthly_appreciation_rate': asset.yearly_appreciation_rate / 12,
        'yearly_appreciation_rate': asset.yearly_appreciation_rate,
        'annual_maintenance_cost': asset.annual_maintenance_cost,
        'remaining_useful_life_years': calculate_remaining_useful_life_years(asset),
        'remaining_useful_life_months': calculate_remaining_useful_life_months(asset),
        'remaining_residual_value': calculate_remaining_residual_value(asset),
        'valuation_method_explanation': get_valuation_method_explanation(asset.valuation_method),
        'depreciation_warning': generate_depreciation_warning(asset)}
    return detailed_info


def explain_scenario_keys(asset, year, scenarios):
    scenario = next((s for s in scenarios if s['year'] == year), None)
    if not scenario:
        return {'error': 'Year not found in scenarios.'}

    explanation = {
        'mean_value': f"The average value of the asset is ${scenario['mean_value']}, which is the most likely value it could have in year {year}.",
        'std_dev': f"The value could vary by about ${scenario['std_dev']} from the mean value, indicating some uncertainty in the asset's future value. This means the actual value could be higher or lower than the average.",
        'percentile_5': f"In the worst-case scenario, the asset's value could drop to ${scenario['percentile_5']} in year {year}. This is the value below which 5% of the simulations fall.",
        'percentile_25': f"In a less favorable scenario, the asset's value could be around ${scenario['percentile_25']} in year {year}. This is the value below which 25% of the simulations fall.",
        'percentile_75': f"In a more favorable scenario, the asset's value could be around ${scenario['percentile_75']} in year {year}. This is the value below which 75% of the simulations fall.",
        'percentile_95': f"In the best-case scenario, the asset's value could rise to ${scenario['percentile_95']} in year {year}. This is the value below which 95% of the simulations fall.",
        'best_case': f"If everything goes perfectly, the asset's value could reach ${scenario['best_case']} in year {year}.",
        'worst_case': f"If things go poorly, the asset's value could drop to ${scenario['worst_case']} in year {year}.",
        'most_likely': f"Given all the possibilities, the most probable value for the asset in year {year} is ${scenario['most_likely']}.",
        'story': scenario['story']
    }

    return explanation


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

# def generate_income_statement(business, year=None, start_date=None, end_date=None, period='monthly'):
#     if year:
#         income = Income.objects.filter(business=business, date__year=year)
#         expense = Expense.objects.filter(business=business, date__year=year)
#     elif start_date and end_date:
#         income = Income.objects.filter(business=business, date__range=(start_date, end_date))
#         expense = Expense.objects.filter(business=business, date__range=(start_date, end_date))
#     elif all([year, start_date, end_date]):
#         income = Income.objects.filter(business=business, date__range=(start_date, end_date))
#         expense = Expense.objects.filter(business=business, date__range=(start_date, end_date))
#     else:
#         income = Income.objects.filter(business=business)
#         expense = Expense.objects.filter(business=business)
#
#     income_by_source = income.values('source').annotate(total_income=Sum('amount')).order_by('source')
#     income_by_category = expense.values('expense_category').annotate(total_income=Sum('amount')).order_by(
#         'expense_category')
#     if period == 'monthly':
#         income_by_month = income.values('date__month').annotate(total_income=Sum('amount')).order_by('date__month')
#         expenses_by_month = expense.values('date__month').annotate(total_income=Sum('amount')).order_by('date__month')
#
#     elif period == 'quarterly':
#         income_by_quarter = income.values('date__year', 'date__quarter').annotate(total_income=Sum('amount')).order_by(
#             'date__year', 'date__quarter')
#         expense_by_quarter = expense.values('date__year', 'date__quarter').annotate(
#             total_expenses=Sum('amount')).order_by('date__year', 'date__quarter')
#
#     elif period == 'yearly':
#         income_by_yearly = income.values('date__year').annotate(total_income=Sum('amount')).order_by('date__year')
#         expenses_by_yearly = expense.values('date__year').annotate(total_income=Sum('amount')).order_by('date__year')
#
#     return {
#         'income_by_source': list(income_by_source),
#         'expenses_by_category': list(income_by_category),
#         'income_by_period': list(
#             income_by_month if period == 'monthly' else income_by_quarter if period == 'quarterly' else income_by_yearly),
#         'expenses_by_period': list(
#             expenses_by_month if period == 'monthly' else expense_by_quarter if period == 'quarterly' else expenses_by_yearly),
#     }
#
#
# def generate_balance_sheet(business, date=None):
#     if date:
#         assets = Asset.objects.filter(business=business, date_acquired__lte=date)
#         liabilities = Liability.objects.filter(business=business, date_incurred__lte=date)
#
#     else:
#         date = date.today()
#         assets = Asset.objects.filter(business=business, date_acquired__lte=date)
#         liabilities = Liability.objects.filter(business=business, date_incurred__lte=date)
#
#     total_assets = calculate_total_assets(assets)
#     total_liabilities = calculate_total_liabilities(liabilities)
#     total_equity = total_assets - total_liabilities
#
#     balance_sheet_data = {
#         'total_assets': f"{total_assets:.2f}",
#         'total_liabilities': f"{total_liabilities:.2f}",
#         'total_equity': f"{total_equity:.2f}"
#     }
#
#
# def reconcile_transactions(business):
#     transactions = Transaction.objects.filter(business=business)
#     reconciled_transactions = []
#     unreconciled_transactions = []
#
#     for transaction in transactions:
#         if transaction.is_reconciled:
#             continue
#
#         matched_statement = BankStatement.objects.filter(
#             business=business,
#             account_number=transaction.account_number,
#             amount=transaction.date,
#             transaction_type=transaction.transaction_types
#         ).first()
#
#         if matched_statement:
#             transaction.is_reconciled = True
#             transaction.matched_statement = matched_statement
#             transaction.save()
#             matched_statement.is_reconciled = True
#             matched_statement.save()
#             reconciled_transactions.append(transaction)
#
#         else:
#             unreconciled_transactions.append(transaction)
#
#     return reconciled_transactions, unreconciled_transactions
#
#
# def generate_income_statement_charts(income_data, expense_data, period):
#     income_df = pd.DataFrame(income_data)
#     expense_df = pd.DataFrame(expense_data)
#
#     income_df['date'] = pd.DataFrame(income_data)
#     expense_df['date'] = pd.DataFrame(expense_data)
#
#     income_df.set_index('date', inplace=True)
#     expense_df.set_index('date', inplace=True)
#     income_time_series = income_df.resample(period).sum()
#     expense_time_series = expense_df.resample(period).sum()
#
#     return {
#         'income_data': income_df.to_dict(),
#         'expense_data': expense_df.to_dict(),
#         'income_time_series': income_time_series.to_dict(),
#         'expense_time_series': expense_time_series.to_dict()
#     }
