"""
Uncertainty Engine — Macro Data, Monte Carlo Simulation, Scenario Forecasting

Implements:
- MacroSnapshot: stores current Nigerian macro parameters (CBN rate, inflation, FX)
- ScenarioForecast: stores generated scenarios for a business
- Cash Flow at Risk (CFaR) via Monte Carlo simulation
- Stress testing under adverse macro conditions
- World Bank API integration for real-time data ingestion

Data sources:
1. Manual admin entry (always available)
2. World Bank API (free, reliable, programmatic)
3. CBN Statistics scraping (future enhancement)
"""

from decimal import Decimal
from django.conf import settings
from django.db import models

from users.models import Business


class MacroSnapshot(models.Model):
    """
    A point-in-time snapshot of Nigerian macro-economic parameters.

    These values drive the Uncertainty Engine's calculations:
    - Asset depreciation/appreciation adjustments
    - Loan real-cost-of-borrowing (Fisher equation)
    - Cash Flow at Risk simulations
    - Opportunity cost calculations

    Can be updated via:
    - Admin panel (manual)
    - Management command `python manage.py fetch_macro_data` (World Bank API)
    - Future: scheduled Celery task for auto-refresh
    """

    class DataSource(models.TextChoices):
        MANUAL = 'MANUAL', 'Manual Entry'
        WORLD_BANK = 'WORLD_BANK', 'World Bank API'
        CBN = 'CBN', 'CBN Statistics'
        NBS = 'NBS', 'NBS Open Data'
        TRADING_ECONOMICS = 'TRADING_ECONOMICS', 'Trading Economics'

    # Core rates
    cbn_monetary_policy_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('26.50'),
        help_text='CBN Monetary Policy Rate (MPR) in %'
    )
    inflation_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('33.48'),
        help_text='Annual inflation rate (CPI) in %'
    )
    inflation_rate_monthly = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('2.29'),
        help_text='Monthly inflation rate in %'
    )

    # Exchange rates
    fx_rate_usd_ngn = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1550.00'),
        help_text='USD/NGN official exchange rate'
    )
    fx_rate_usd_ngn_parallel = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1600.00'),
        help_text='USD/NGN parallel market rate'
    )

    # Interest rates
    prime_lending_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('30.00'),
        help_text='Average prime lending rate in %'
    )
    savings_deposit_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('5.50'),
        help_text='Average savings deposit rate in %'
    )
    treasury_bill_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('18.00'),
        help_text='91-day Treasury Bill rate in %'
    )

    # Energy costs (critical for Nigerian businesses)
    diesel_price_per_litre = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('1300.00'),
        help_text='Diesel price per litre in NGN'
    )
    petrol_price_per_litre = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal('700.00'),
        help_text='PMS/Petrol price per litre in NGN'
    )

    # GDP and growth
    gdp_growth_rate = models.DecimalField(
        max_digits=6, decimal_places=2, default=Decimal('3.46'),
        help_text='Annual GDP growth rate in %'
    )

    # Metadata
    effective_date = models.DateField(
        help_text='The date these macro parameters are effective from'
    )
    source = models.CharField(
        max_length=25, choices=DataSource.choices,
        default=DataSource.MANUAL
    )
    notes = models.TextField(blank=True, default='')
    is_current = models.BooleanField(
        default=True,
        help_text='Whether this is the currently active macro snapshot'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date']
        get_latest_by = 'effective_date'

    def __str__(self):
        return (
            f"Macro Snapshot ({self.effective_date}) — "
            f"MPR: {self.cbn_monetary_policy_rate}%, "
            f"Inflation: {self.inflation_rate}%"
        )

    def save(self, *args, **kwargs):
        # Ensure only one snapshot is marked as current
        if self.is_current:
            MacroSnapshot.objects.filter(is_current=True).update(is_current=False)
        super().save(*args, **kwargs)

    @classmethod
    def get_current(cls):
        """Get the most recent active macro snapshot."""
        try:
            return cls.objects.filter(is_current=True).latest()
        except cls.DoesNotExist:
            return cls.objects.latest() if cls.objects.exists() else None

    @property
    def real_interest_rate(self):
        """Fisher equation: real rate ≈ nominal rate - inflation rate."""
        return float(self.cbn_monetary_policy_rate) - float(self.inflation_rate)

    @property
    def adjusted_rate(self):
        """Combined adjustment factor for opportunity cost calculations."""
        r = float(self.cbn_monetary_policy_rate) / 100
        i = float(self.inflation_rate) / 100
        return (1 + r) * (1 + i) - 1


class ScenarioForecast(models.Model):
    """
    Stores the results of a scenario forecast (Monte Carlo or deterministic).

    Generated by the Uncertainty Engine for a specific business and forecast type.
    """

    class ForecastType(models.TextChoices):
        CASH_FLOW = 'CASH_FLOW', 'Cash Flow at Risk'
        ASSET_VALUE = 'ASSET_VALUE', 'Asset Valuation'
        LOAN_STRESS = 'LOAN_STRESS', 'Loan Stress Test'
        REVENUE = 'REVENUE', 'Revenue Forecast'
        EXPENSE = 'EXPENSE', 'Expense Forecast'

    business = models.ForeignKey(
        Business, on_delete=models.CASCADE, related_name='scenario_forecasts'
    )
    forecast_type = models.CharField(
        max_length=20, choices=ForecastType.choices
    )
    macro_snapshot = models.ForeignKey(
        MacroSnapshot, on_delete=models.SET_NULL, null=True, blank=True,
        help_text='The macro snapshot used for this forecast'
    )

    # Scenario results (stored as JSON-compatible decimal values)
    base_case = models.DecimalField(max_digits=20, decimal_places=2)
    optimistic_case = models.DecimalField(max_digits=20, decimal_places=2)
    pessimistic_case = models.DecimalField(max_digits=20, decimal_places=2)
    stress_case = models.DecimalField(max_digits=20, decimal_places=2)

    # Statistical metrics
    mean_value = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    std_deviation = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    confidence_interval_lower = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    confidence_interval_upper = models.DecimalField(
        max_digits=20, decimal_places=2, null=True, blank=True
    )
    confidence_level = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('95.00'),
        help_text='Confidence level in %'
    )

    # Simulation parameters
    num_simulations = models.PositiveIntegerField(default=10000)
    forecast_horizon_months = models.PositiveIntegerField(default=12)

    # Metadata
    parameters_json = models.JSONField(
        default=dict, blank=True,
        help_text='Full simulation parameters as JSON'
    )
    results_json = models.JSONField(
        default=dict, blank=True,
        help_text='Detailed simulation results as JSON'
    )
    generated_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='scenario_forecasts'
    )

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        return (
            f"{self.forecast_type} forecast for {self.business} "
            f"({self.generated_at.date()})"
        )


class MacroDataLog(models.Model):
    """
    Audit log for macro data fetch operations.
    Tracks when data was fetched, from what source, and whether it succeeded.
    """

    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        PARTIAL = 'PARTIAL', 'Partial Success'

    source = models.CharField(max_length=25, choices=MacroSnapshot.DataSource.choices)
    status = models.CharField(max_length=10, choices=Status.choices)
    indicators_fetched = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default='')
    response_data = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fetched_at']

    def __str__(self):
        return f"Macro fetch: {self.source} — {self.status} ({self.fetched_at})"
