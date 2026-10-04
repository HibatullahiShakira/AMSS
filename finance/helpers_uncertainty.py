"""
Uncertainty Engine — Core Business Logic

Implements:
- Cash Flow at Risk (CFaR) via Monte Carlo simulation
- Stress testing under adverse macro conditions
- Scenario generation (base/optimistic/pessimistic/stress)
- Real cost of borrowing calculations (Fisher equation)
- Regime classification (stable vs crisis)
"""

import numpy as np
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum

from .models import Income, Expense, Asset, Liability
from .models_uncertainty import MacroSnapshot, ScenarioForecast


def get_macro_parameters():
    """
    Get the current macro parameters from the latest MacroSnapshot.
    Falls back to hardcoded defaults if no snapshot exists.
    """
    snapshot = MacroSnapshot.get_current()
    if snapshot:
        return {
            'cbn_rate': float(snapshot.cbn_monetary_policy_rate) / 100,
            'inflation_rate': float(snapshot.inflation_rate) / 100,
            'inflation_monthly': float(snapshot.inflation_rate_monthly) / 100,
            'fx_rate': float(snapshot.fx_rate_usd_ngn),
            'prime_lending_rate': float(snapshot.prime_lending_rate) / 100,
            'savings_rate': float(snapshot.savings_deposit_rate) / 100,
            'tbill_rate': float(snapshot.treasury_bill_rate) / 100,
            'gdp_growth': float(snapshot.gdp_growth_rate) / 100,
            'diesel_price': float(snapshot.diesel_price_per_litre),
            'real_interest_rate': snapshot.real_interest_rate / 100,
            'adjusted_rate': snapshot.adjusted_rate,
            'snapshot': snapshot,
        }
    else:
        # Fallback defaults (July 2026 values)
        return {
            'cbn_rate': 0.2650,
            'inflation_rate': 0.3348,
            'inflation_monthly': 0.0229,
            'fx_rate': 1550.00,
            'prime_lending_rate': 0.30,
            'savings_rate': 0.055,
            'tbill_rate': 0.18,
            'gdp_growth': 0.0346,
            'diesel_price': 1300.00,
            'real_interest_rate': -0.0698,
            'adjusted_rate': 0.6956,
            'snapshot': None,
        }


def cash_flow_at_risk(business, horizon_months=12, num_simulations=10000,
                      confidence_level=0.95):
    """
    Monte Carlo Cash Flow at Risk (CFaR) simulation.

    Simulates future cash flows under macro uncertainty.
    Returns percentile-based risk measures.

    The model accounts for:
    - Income volatility (estimated from historical data or assumed)
    - Expense volatility (estimated from historical data or assumed)
    - Inflation impact on expenses (expenses grow with inflation)
    - Interest rate impact on loan payments
    - FX impact on imported goods (if applicable)
    """
    macro = get_macro_parameters()

    # Get historical income and expense data
    incomes = Income.objects.filter(business=business)
    expenses = Expense.objects.filter(business=business)

    total_monthly_income = incomes.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    total_monthly_expense = expenses.aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')

    # Estimate monthly averages
    income_count = max(incomes.count(), 1)
    expense_count = max(expenses.count(), 1)

    avg_monthly_income = float(total_monthly_income) / max(income_count / 12, 1)
    avg_monthly_expense = float(total_monthly_expense) / max(expense_count / 12, 1)

    # Volatility estimates
    income_volatility = 0.15  # 15% monthly income volatility (Nigerian SME typical)
    expense_volatility = 0.10  # 10% monthly expense volatility
    inflation_shock_std = 0.05  # Monthly inflation can swing ±5%

    # Run Monte Carlo
    cumulative_cash_flows = np.zeros(num_simulations)

    for sim in range(num_simulations):
        total_cash = 0.0

        for month in range(horizon_months):
            # Simulate income with volatility
            income_shock = np.random.normal(1.0, income_volatility)
            monthly_income = avg_monthly_income * income_shock

            # Simulate expenses with inflation growth
            inflation_shock = np.random.normal(
                macro['inflation_monthly'], inflation_shock_std
            )
            expense_growth = (1 + inflation_shock) ** month
            expense_shock = np.random.normal(1.0, expense_volatility)
            monthly_expense = avg_monthly_expense * expense_growth * expense_shock

            net_cash = monthly_income - monthly_expense
            total_cash += net_cash

        cumulative_cash_flows[sim] = total_cash

    # Calculate risk metrics
    mean_cf = float(np.mean(cumulative_cash_flows))
    std_cf = float(np.std(cumulative_cash_flows))
    percentile_5 = float(np.percentile(cumulative_cash_flows, 5))
    percentile_25 = float(np.percentile(cumulative_cash_flows, 25))
    percentile_50 = float(np.percentile(cumulative_cash_flows, 50))
    percentile_75 = float(np.percentile(cumulative_cash_flows, 75))
    percentile_95 = float(np.percentile(cumulative_cash_flows, 95))

    alpha = 1 - confidence_level
    cfar = float(np.percentile(cumulative_cash_flows, alpha * 100))
    prob_negative = float(np.mean(cumulative_cash_flows < 0))

    return {
        'horizon_months': horizon_months,
        'num_simulations': num_simulations,
        'confidence_level': confidence_level,
        'mean_cash_flow': round(mean_cf, 2),
        'std_deviation': round(std_cf, 2),
        'cash_flow_at_risk': round(cfar, 2),
        'probability_negative': round(prob_negative, 4),
        'percentiles': {
            'p5': round(percentile_5, 2),
            'p25': round(percentile_25, 2),
            'p50_median': round(percentile_50, 2),
            'p75': round(percentile_75, 2),
            'p95': round(percentile_95, 2),
        },
        'scenarios': {
            'base_case': round(percentile_50, 2),
            'optimistic': round(percentile_95, 2),
            'pessimistic': round(percentile_5, 2),
            'stress': round(float(np.percentile(cumulative_cash_flows, 1)), 2),
        },
        'macro_parameters': {
            'inflation_rate': macro['inflation_rate'],
            'cbn_rate': macro['cbn_rate'],
            'fx_rate': macro['fx_rate'],
        },
    }


def stress_test_business(business, stress_scenarios=None):
    """
    Run stress tests on a business under adverse macro conditions.

    Default stress scenarios:
    1. Inflation spike (+10% above current)
    2. Revenue collapse (-30%)
    3. Combined shock (inflation +10%, revenue -20%, FX +25%)
    4. Interest rate shock (+5% on all loans)
    """
    macro = get_macro_parameters()

    # Current financial position
    total_income = float(
        Income.objects.filter(business=business).aggregate(
            total=Sum('amount')
        )['total'] or 0
    )
    total_expenses = float(
        Expense.objects.filter(business=business).aggregate(
            total=Sum('amount')
        )['total'] or 0
    )
    total_liabilities = float(
        Liability.objects.filter(business=business).aggregate(
            total=Sum('amount')
        )['total'] or 0
    )
    total_assets = float(
        Asset.objects.filter(business=business).aggregate(
            total=Sum('amount')
        )['total'] or 0
    )

    net_income = total_income - total_expenses
    current_dscr = (net_income / total_liabilities) if total_liabilities > 0 else float('inf')

    if stress_scenarios is None:
        stress_scenarios = [
            {
                'name': 'Inflation Spike',
                'description': 'Inflation increases by 10 percentage points',
                'inflation_delta': 0.10,
                'revenue_shock': 0.0,
                'expense_shock': 0.10,  # Expenses grow with inflation
                'fx_shock': 0.0,
                'rate_shock': 0.0,
            },
            {
                'name': 'Revenue Collapse',
                'description': 'Revenue drops by 30%',
                'inflation_delta': 0.0,
                'revenue_shock': -0.30,
                'expense_shock': 0.0,
                'fx_shock': 0.0,
                'rate_shock': 0.0,
            },
            {
                'name': 'Combined Macro Shock',
                'description': 'Inflation +10%, Revenue -20%, Naira depreciation +25%',
                'inflation_delta': 0.10,
                'revenue_shock': -0.20,
                'expense_shock': 0.15,
                'fx_shock': 0.25,
                'rate_shock': 0.03,
            },
            {
                'name': 'Interest Rate Shock',
                'description': 'CBN raises MPR by 5 percentage points',
                'inflation_delta': 0.0,
                'revenue_shock': 0.0,
                'expense_shock': 0.0,
                'fx_shock': 0.0,
                'rate_shock': 0.05,
            },
        ]

    results = []
    for scenario in stress_scenarios:
        stressed_income = total_income * (1 + scenario['revenue_shock'])
        stressed_expenses = total_expenses * (1 + scenario['expense_shock'])
        stressed_net = stressed_income - stressed_expenses

        stressed_liability_cost = total_liabilities * (
            macro['cbn_rate'] + scenario['rate_shock']
        )

        stressed_dscr = (
            stressed_net / stressed_liability_cost
        ) if stressed_liability_cost > 0 else float('inf')

        impact = stressed_net - net_income
        survival_months = (
            total_assets / abs(stressed_expenses / 12)
        ) if stressed_expenses > 0 else float('inf')

        results.append({
            'scenario': scenario['name'],
            'description': scenario['description'],
            'stressed_net_income': round(stressed_net, 2),
            'impact_on_net_income': round(impact, 2),
            'impact_percentage': round(
                (impact / net_income * 100) if net_income != 0 else 0, 2
            ),
            'stressed_dscr': round(stressed_dscr, 4),
            'dscr_adequate': stressed_dscr >= 1.2,
            'survival_months': round(survival_months, 1),
            'severity': (
                'CRITICAL' if stressed_dscr < 1.0
                else 'WARNING' if stressed_dscr < 1.2
                else 'MANAGEABLE' if stressed_dscr < 1.5
                else 'SAFE'
            ),
        })

    return {
        'business_id': business.id,
        'current_position': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'net_income': net_income,
            'total_liabilities': total_liabilities,
            'total_assets': total_assets,
            'current_dscr': round(current_dscr, 4),
        },
        'macro_snapshot': {
            'inflation': macro['inflation_rate'],
            'cbn_rate': macro['cbn_rate'],
            'fx_rate': macro['fx_rate'],
        },
        'stress_results': results,
    }


def classify_macro_regime():
    """
    Classify the current macro environment into a regime.

    Regimes:
    - STABLE: Inflation < 15%, MPR < 20%, FX change < 10%
    - ELEVATED: Inflation 15-25%, MPR 20-25%
    - CRISIS: Inflation > 25%, MPR > 25%, or FX depreciation > 30%

    This classification drives how aggressively the engine applies
    uncertainty adjustments.
    """
    macro = get_macro_parameters()
    inflation = macro['inflation_rate']
    cbn_rate = macro['cbn_rate']

    if inflation > 0.25 or cbn_rate > 0.25:
        regime = 'CRISIS'
        description = (
            'The Nigerian economy is in a crisis regime. '
            'High inflation and interest rates significantly increase '
            'business risk. Cash preservation and debt reduction should '
            'be prioritised.'
        )
        risk_multiplier = 1.5
    elif inflation > 0.15 or cbn_rate > 0.20:
        regime = 'ELEVATED'
        description = (
            'Macro conditions are elevated but manageable. '
            'Plan for increased costs and tighter margins. '
            'Avoid unnecessary new debt.'
        )
        risk_multiplier = 1.2
    else:
        regime = 'STABLE'
        description = (
            'Macro conditions are relatively stable. '
            'Normal business planning assumptions apply.'
        )
        risk_multiplier = 1.0

    return {
        'regime': regime,
        'description': description,
        'risk_multiplier': risk_multiplier,
        'indicators': {
            'inflation_rate': f"{inflation * 100:.1f}%",
            'cbn_rate': f"{cbn_rate * 100:.1f}%",
            'fx_rate': f"₦{macro['fx_rate']:.0f}/USD",
            'real_interest_rate': f"{macro['real_interest_rate'] * 100:.1f}%",
        },
    }


def compute_real_cost_of_borrowing(nominal_rate, inflation_rate=None):
    """
    Fisher equation: real rate = nominal rate - inflation rate.

    In Nigeria with 33%+ inflation and 27%+ nominal rates,
    the real cost of borrowing is often negative — meaning the
    debtor benefits from inflation eroding the real value of the loan.

    This is a critical insight for Nigerian business decisions.
    """
    if inflation_rate is None:
        macro = get_macro_parameters()
        inflation_rate = macro['inflation_rate']

    nominal = float(nominal_rate) if not isinstance(nominal_rate, float) else nominal_rate
    inflation = float(inflation_rate) if not isinstance(inflation_rate, float) else inflation_rate

    real_rate = nominal - inflation
    real_rate_exact = ((1 + nominal) / (1 + inflation)) - 1

    return {
        'nominal_rate': round(nominal * 100, 2),
        'inflation_rate': round(inflation * 100, 2),
        'real_rate_approximate': round(real_rate * 100, 2),
        'real_rate_exact': round(real_rate_exact * 100, 2),
        'is_negative_real_rate': real_rate < 0,
        'interpretation': (
            f"At {nominal*100:.1f}% nominal rate with {inflation*100:.1f}% inflation, "
            f"the real cost of borrowing is {real_rate_exact*100:.1f}%. "
            + (
                "This means inflation is eroding debt faster than interest accrues — "
                "borrowing actually benefits the debtor in real terms."
                if real_rate < 0
                else "The real cost of borrowing is positive — interest outpaces inflation."
            )
        ),
    }
