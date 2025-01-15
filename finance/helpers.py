from datetime import date, timedelta
from decimal import Decimal
from django.db.models import Sum
import numpy as np
from datetime import date
from finance.models import PaymentSchedule, Income, Expense, AccountsReceivable, AccountsPayable
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error
from pmdarima import auto_arima
from django.db import models


def perform_projection(business, period, forecast_steps, seasonal_period):
    incomes = list(Income.objects.filter(business=business).values('date', 'amount'))
    expenses = list(Expense.objects.filter(business=business).values('date', 'amount'))

    if not incomes:
        raise ValueError("No income data found for the business.")
    if not expenses:
        raise ValueError("No expense data found for the business.")

    df_incomes = pd.DataFrame(incomes)
    df_expenses = pd.DataFrame(expenses)

    df_incomes['amount'] = pd.to_numeric(df_incomes['amount'], errors='coerce')
    df_expenses['amount'] = pd.to_numeric(df_expenses['amount'], errors='coerce')

    if 'date' not in df_incomes.columns or 'date' not in df_expenses.columns:
        raise KeyError("'date' column missing from income or expense data.")

    df_incomes.sort_values('date', inplace=True)
    df_expenses.sort_values('date', inplace=True)
    df_incomes.rename(columns={'amount': 'inflow'}, inplace=True)
    df_expenses.rename(columns={'amount': 'outflow'}, inplace=True)
    df = pd.merge(df_incomes, df_expenses, on='date', how='outer').fillna(0)
    df['net_cash_flow'] = df['inflow'] - df['outflow']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    if period == 'daily':
        cash_flow = df.resample('D').sum()['net_cash_flow']
    elif period == 'weekly':
        cash_flow = df.resample('W').sum()['net_cash_flow']
    elif period == 'bi-weekly':
        cash_flow = df.resample('2W').sum()['net_cash_flow']
    elif period == 'quarterly':
        cash_flow = df.resample('Q').sum()['net_cash_flow']
    elif period == 'yearly':
        cash_flow = df.resample('Y').sum()['net_cash_flow']
    else:
        cash_flow = df.resample('M').sum()['net_cash_flow']

    print("Cash Flow:")
    print(cash_flow)

    model = auto_arima(cash_flow, seasonal=True, m=seasonal_period,
                       stepwise=True, trace=True, error_action='ignore', suppress_warnings=True)

    print("Best SARIMA Model:")
    print(model.summary())

    mse = mean_squared_error(cash_flow, model.predict_in_sample())
    mae = mean_absolute_error(cash_flow, model.predict_in_sample())

    forecast = model.predict(n_periods=forecast_steps)
    predictions = []

    if period == 'daily':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(days=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_cash_flow': float(forecast[i])
            })
    elif period == 'weekly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(weeks=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%W%U'),
                'predicted_cash_flow': float(forecast[i])
            })
    elif period == 'bi-weekly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(weeks=2 * (i + 1))
            predictions.append({
                'date': date.strftime('%Y-%W%U'),
                'predicted_cash_flow': float(forecast[i])
            })
    elif period == 'quarterly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(months=3 * (i + 1))
            predictions.append({
                'date': date.strftime('%Y-Q{}').format((date.month - 1) // 3 + 1),
                'predicted_cash_flow': float(forecast[i])
            })
    elif period == 'yearly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(years=i + 1)
            predictions.append({
                'date': date.strftime('%Y'),
                'predicted_cash_flow': float(forecast[i])
            })
    else:
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(months=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%m'),
                'predicted_cash_flow': float(forecast[i])
            })

    return {
        "predictions": predictions,
        "mse": mse,
        "mae": mae
    }


def perform_cash_outflow_projection(business, period, forecast_steps, seasonal_period):
    expenses = list(Expense.objects.filter(business=business).values('date', 'amount'))

    if not expenses:
        raise ValueError("No expense data found for the business.")

    df_expenses = pd.DataFrame(expenses)
    df_expenses['amount'] = pd.to_numeric(df_expenses['amount'], errors='coerce')

    if 'date' not in df_expenses.columns:
        raise KeyError("'date' column missing from expense data.")

    df_expenses.sort_values('date', inplace=True)
    df_expenses.rename(columns={'amount': 'outflow'}, inplace=True)
    df_expenses['date'] = pd.to_datetime(df_expenses['date'])
    df_expenses.set_index('date', inplace=True)

    if period == 'daily':
        outflow = df_expenses.resample('D').sum()['outflow']
    elif period == 'weekly':
        outflow = df_expenses.resample('W').sum()['outflow']
    elif period == 'bi-weekly':
        outflow = df_expenses.resample('2W').sum()['outflow']
    elif period == 'quarterly':
        outflow = df_expenses.resample('Q').sum()['outflow']
    elif period == 'yearly':
        outflow = df_expenses.resample('Y').sum()['outflow']
    else:
        outflow = df_expenses.resample('M').sum()['outflow']

    print("Outflow:")
    print(outflow)

    # Use auto_arima for parameter tuning
    model = auto_arima(outflow, seasonal=True, m=seasonal_period,
                       stepwise=True, trace=True, error_action='ignore', suppress_warnings=True)

    print("Best SARIMA Model:")
    print(model.summary())

    mse = mean_squared_error(outflow, model.predict_in_sample())
    mae = mean_absolute_error(outflow, model.predict_in_sample())

    forecast = model.predict(n_periods=forecast_steps)
    predictions = []

    if period == 'daily':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(days=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%m-%d'),
                'predicted_outflow': float(forecast[i])
            })
    elif period == 'weekly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(weeks=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%W%U'),
                'predicted_outflow': float(forecast[i])
            })
    elif period == 'bi-weekly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(weeks=2 * (i + 1))
            predictions.append({
                'date': date.strftime('%Y-%W%U'),
                'predicted_outflow': float(forecast[i])
            })
    elif period == 'quarterly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(months=3 * (i + 1))
            predictions.append({
                'date': date.strftime('%Y-Q{}').format((date.month - 1) // 3 + 1),
                'predicted_outflow': float(forecast[i])
            })
    elif period == 'yearly':
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(years=i + 1)
            predictions.append({
                'date': date.strftime('%Y'),
                'predicted_outflow': float(forecast[i])
            })
    else:
        for i in range(forecast_steps):
            date = pd.Timestamp.today() + pd.DateOffset(months=i + 1)
            predictions.append({
                'date': date.strftime('%Y-%m'),
                'predicted_outflow': float(forecast[i])
            })

    return {
        "predictions": predictions,
        "mse": mse,
        "mae": mae
    }


def generate_report_based_on_date_range(business, start_date=None, end_date=None):
    incomes = list(Income.objects.filter(business=business).values('date', 'amount'))
    expenses = list(Expense.objects.filter(business=business).values('date', 'amount'))

    if not incomes:
        raise ValueError("No income data found for the business.")
    if not expenses:
        raise ValueError("No expense data found for the business.")

    df_incomes = pd.DataFrame(incomes)
    df_expenses = pd.DataFrame(expenses)
    df_incomes.sort_values('date', inplace=True)
    df_expenses.sort_values('date', inplace=True)
    df_incomes.rename(columns={'amount': 'inflow'}, inplace=True)
    df_expenses.rename(columns={'amount': 'outflow'}, inplace=True)
    df = pd.merge(df_incomes, df_expenses, on='date', how='outer').fillna(0)
    df['net_cash_flow'] = df['inflow'] - df['outflow']

    df['date'] = pd.to_datetime(df['date']).dt.date

    if start_date and end_date:
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    print(df.to_dict)
    return df.to_dict('records')


def generate_report_based_on_period(business, period=None):
    report_data = generate_report_based_on_date_range(business)
    df = pd.DataFrame(report_data)

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    if period == 'monthly':
        report = df.resample('M').sum()
    elif period == 'quarterly':
        report = df.resample('Q').sum()
    elif period == 'yearly':
        report = df.resample('A').sum()
    else:
        raise ValueError("Invalid period specified.")

    report['net_cash_flow'] = report['inflow'] - report['outflow']

    report.reset_index(inplace=True)
    print(f'Final report head:\n{report.head()}')

    return report.to_dict('records')


def calculate_total_pending_receivables(business):
    receivables = AccountsReceivable.objects.filter(business=business, status='Pending')
    total_pending_receivable = receivables.aggregate(total=Sum('amount_due'))['total'] or 0
    return total_pending_receivable


def calculate_total_pending_payables_for_period(business, start_date, end_date):
    payables = AccountsPayable.objects.filter(
        business=business,
        status='Pending',
        due_date__gte=start_date,
        due_date__lte=end_date
    )
    total_pending_payable = payables.aggregate(total=Sum('amount_due'))['total'] or 0
    return total_pending_payable


def calculate_total_pending_payables(business):
    payable = AccountsPayable.objects.filter(business=business, status='Pending')
    total_pending_payable = payable.aggregate(total=Sum('amount_due'))['total'] or 0
    return total_pending_payable


def calculate_total_pending_receivables_for_period(business, start_date, end_date):
    receivables = AccountsReceivable.objects.filter(
        business=business,
        status='Pending',
        due_date__gte=start_date,
        due_date__lte=end_date
    )
    total_pending_receivables = receivables.aggregate(total=Sum('amount_due'))['total'] or 0
    return total_pending_receivables


def calculate_remaining_balance(business):
    total_pending_receivables = calculate_total_pending_receivables(business)
    total_pending_payable = calculate_total_pending_payables(business)
    remaining_balance = total_pending_receivables - total_pending_payable
    return {
        "total_pending_receivables": total_pending_receivables,
        "total_pending_payable": total_pending_payable,
        "remaining_balance": remaining_balance
    }


def calculate_remaining_balance_for_period(business, start_date, end_date):
    total_pending_receivable = calculate_total_pending_receivables_for_period(business, start_date, end_date)
    total_pending_payable = calculate_total_pending_payables_for_period(business, start_date,
                                                                        end_date)
    remaining_balance = total_pending_receivable - total_pending_payable
    return {
        "total_pending_receivables_for_period": total_pending_receivable,
        "total_pending_payable_for_period": total_pending_payable,
        "remaining_balance_for_period": remaining_balance
    }


def calculate_real_time_data(alert_threshold):
    incomes = list(Income.objects.values('date', 'amount'))
    expenses = list(Expense.objects.values('date', 'amount'))

    df_incomes = pd.DataFrame(incomes)
    df_expenses = pd.DataFrame(expenses)

    df_incomes.sort_values('date', inplace=True)
    df_expenses.sort_values('date', inplace=True)

    df_incomes.rename(columns={'amount': 'inflow'}, inplace=True)
    df_expenses.rename(columns={'amount': 'outflow'}, inplace=True)

    df = pd.merge(df_incomes, df_expenses, on='date', how='outer').fillna(0)
    df['net_cash_flow'] = df['inflow'] - df['outflow']

    real_time_data = df.to_dict('records')

    alerts = []
    for entry in real_time_data:
        if entry['net_cash_flow'] < alert_threshold:
            alerts.append(f"Alert! Net cash flow on {entry['date']} is below the threshold of {alert_threshold}. Current net cash flow is: {entry['net_cash_flow']}")

    return real_time_data, alerts


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

    if not depreciation_rate and not is_appreciating:
        depreciation_rate = (float(asset.amount) - float(asset.residual_value)) / (
                float(asset.amount) * asset.useful_life)

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
            'mean_value': round(mean_future_values[year], 2),
            'std_dev': round(std_dev_future_values[year], 2),
            'percentile_25': round(percentile_25[year], 2),
            'percentile_75': round(percentile_75[year], 2),
            'percentile_5': round(percentile_5[year], 2),
            'percentile_95': round(percentile_95[year], 2),
            'best_case': round(percentile_95[year], 2),
            'worst_case': round(percentile_5[year], 2),
            'most_likely': round(mean_future_values[year], 2)
        }

        scenarios.append(scenario)

    return scenarios


def generate_asset_report(asset, year, scenarios, risk_tolerance="moderate"):
    scenario = next((s for s in scenarios if s['year'] == year), None)
    if not scenario:
        return "Scenario not found for the given year."

    story = f"In year {year}, your {asset.name} is expected to be worth around ${scenario['most_likely']}.\n"

    if risk_tolerance == "low":
        story += f"There's a possibility the value could drop as low as ${scenario['worst_case']}. "
        story += "To minimize potential losses, consider:\n"
        story += "  - **Regular maintenance:** Ensure proper maintenance to extend the asset's lifespan.\n"
        story += "  - **Diversification:** Spread your investments across different assets to reduce overall risk.\n"
        story += "  - **Insurance:** Explore insurance options to protect against unforeseen damage or loss.\n"
    elif risk_tolerance == "high":
        story += f"On the bright side, the value could potentially reach as high as ${scenario['best_case']}. "
        story += "To capitalize on potential gains:\n"
        story += "  - **Invest in upgrades:** Consider upgrading the asset to enhance its performance and value.\n"
        story += ("- **Explore potential for increased utilization:** Find ways to increase the asset's usage and "
                  "generate more revenue.\n")
    else:
        story += f"The range of potential values falls between ${scenario['percentile_25']} and ${scenario['percentile_75']}. "
        story += "To navigate this uncertainty:\n"
        story += ("- **Monitor market trends:** Stay informed about market conditions that could affect the asset's "
                  "value.\n")
        story += ("- **Regularly review your investment strategy:** Adjust your strategy based on market changes and "
                  "your financial goals.\n")

    if asset.is_appreciating:
        story += ("As this asset is expected to appreciate, consider holding onto it for the long term to potentially "
                  "realize significant gains.\n")
    else:
        warnings = generate_depreciation_warning(asset)
        if warnings:
            story += f"Watch out for potential depreciation due to {', '.join(warnings)}. "
            story += ("Consider these factors when making decisions about the asset's future and potential replacement "
                      "options.\n")

    return story


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
    scenario = [s for s in scenarios if s['year'] == year]
    if not scenario:
        return "Scenario not found for the given year."
    scenario = scenario[0]  # Extract the first (and only) element from the list

    explanation = {
        'year': year,
        'mean_value': f"The average expected value of the asset for year {year} is ${scenario['mean_value']}.",
        'std_dev': f"Risk: The value might vary by about ${scenario['std_dev']} from the average.",
        'percentile_25': f"25% chance the value will be less than ${scenario['percentile_25']}.",
        'percentile_75': f"75% chance the value will be less than ${scenario['percentile_75']}.",
        'percentile_5': f"5% chance the value will be less than ${scenario['percentile_5']}.",
        'percentile_95': f"95% chance the value will be less than ${scenario['percentile_95']}.",
        'best_case': f"Best possible value in year {year} is ${scenario['best_case']}.",
        'worst_case': f"Worst possible value in year {year} is ${scenario['worst_case']}.",
        'most_likely': f"The value you can most likely expect in year {year} is ${scenario['most_likely']}."
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


def calculate_interest_accrual(liability):
    interest_rate = Decimal(liability.interest_rate)
    amount = Decimal(liability.amount)
    days_since_incurred = (date.today() - liability.date_incurred).days
    interest_accrued = amount * interest_rate * days_since_incurred / 365
    return interest_accrued


def track_loan_payments(liability):
    total_paid = PaymentSchedule.objects.filter(liability=liability).aggregate(Sum('installment_amount'))[
                     'installment_amount__sum'] or Decimal('0.00')
    remaining_balance = Decimal(liability.amount) - total_paid
    return total_paid, remaining_balance


def calculate_remaining_payments(payment_schedule):
    total_payments = (
                             payment_schedule.end_date - payment_schedule.start_date).days // payment_schedule.get_payment_frequency_in_days()
    payments_made = (date.today() - payment_schedule.start_date).days // payment_schedule.get_payment_frequency_in_days
    remaining_payments = total_payments - payments_made
    return remaining_payments


def get_payment_frequency_in_days(payment_frequency):
    payment_frequencies = {
        'Weekly': 7,
        'Bi-Weekly': 14,
        'Monthly': 30,
        'Quarterly': 90,
        'Semi-Annually': 180,
        'Annually': 365,
    }
    return payment_frequencies.get(payment_frequency, 0)


def generate_payment_schedule(principal, interest_rate, term_years, payment_frequency, start_date):
    term_months = term_years * 12
    monthly_interest_rate = Decimal(interest_rate) / Decimal('100') / Decimal('12')
    monthly_payment = principal * monthly_interest_rate / (1 - (1 + monthly_interest_rate) ** -term_months)

    payment_frequencies = {
        'Weekly': 52,
        'Bi-Weekly': 26,
        'Monthly': 12,
        'Quarterly': 4,
        'Semi-Annually': 2,
        'Annually': 1,
    }
    num_payments_per_year = Decimal(payment_frequencies[payment_frequency])
    payment_interval_days = Decimal(365) // num_payments_per_year

    payments = []
    remaining_principal = principal
    total_payments = int(term_years * num_payments_per_year)
    for i in range(total_payments):
        interest_for_period = remaining_principal * (monthly_interest_rate * 12 / num_payments_per_year)
        principal_for_period = monthly_payment / (12 / num_payments_per_year) - interest_for_period
        payment_date = start_date + timedelta(days=int(i * payment_interval_days))
        remaining_principal -= principal_for_period
        payments.append({
            'date': payment_date,
            'principal': principal_for_period,
            'interest': interest_for_period,
            'remaining_principal': remaining_principal
        })

    return payments


def calculate_current_ratio(current_assets, current_liabilities):
    return current_assets / current_liabilities

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
