"""
Uncertainty Engine Serializers
"""

from rest_framework import serializers

from .models_uncertainty import MacroSnapshot, ScenarioForecast, MacroDataLog


class MacroSnapshotSerializer(serializers.ModelSerializer):
    real_interest_rate = serializers.FloatField(read_only=True)
    adjusted_rate = serializers.FloatField(read_only=True)

    class Meta:
        model = MacroSnapshot
        fields = [
            'id', 'cbn_monetary_policy_rate', 'inflation_rate',
            'inflation_rate_monthly', 'fx_rate_usd_ngn',
            'fx_rate_usd_ngn_parallel', 'prime_lending_rate',
            'savings_deposit_rate', 'treasury_bill_rate',
            'diesel_price_per_litre', 'petrol_price_per_litre',
            'gdp_growth_rate', 'effective_date', 'source', 'notes',
            'is_current', 'real_interest_rate', 'adjusted_rate',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['created_at', 'updated_at']


class MacroSnapshotSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing macro snapshots."""
    class Meta:
        model = MacroSnapshot
        fields = [
            'id', 'effective_date', 'cbn_monetary_policy_rate',
            'inflation_rate', 'fx_rate_usd_ngn', 'source', 'is_current',
        ]


class ScenarioForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScenarioForecast
        fields = [
            'id', 'business', 'forecast_type', 'macro_snapshot',
            'base_case', 'optimistic_case', 'pessimistic_case', 'stress_case',
            'mean_value', 'std_deviation',
            'confidence_interval_lower', 'confidence_interval_upper',
            'confidence_level', 'num_simulations', 'forecast_horizon_months',
            'parameters_json', 'results_json',
            'generated_at', 'user',
        ]
        read_only_fields = ['generated_at']


class MacroDataLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MacroDataLog
        fields = [
            'id', 'source', 'status', 'indicators_fetched',
            'error_message', 'response_data', 'fetched_at',
        ]


class CFaRInputSerializer(serializers.Serializer):
    """Input parameters for Cash Flow at Risk simulation."""
    horizon_months = serializers.IntegerField(
        default=12, min_value=1, max_value=60
    )
    num_simulations = serializers.IntegerField(
        default=10000, min_value=1000, max_value=100000
    )
    confidence_level = serializers.FloatField(
        default=0.95, min_value=0.80, max_value=0.99
    )


class RealCostInputSerializer(serializers.Serializer):
    """Input for real cost of borrowing calculation."""
    nominal_rate = serializers.FloatField(
        help_text='Nominal interest rate as decimal (e.g. 0.32 for 32%)'
    )
    inflation_rate = serializers.FloatField(
        required=False,
        help_text='Override inflation rate (uses current macro snapshot if not provided)'
    )
