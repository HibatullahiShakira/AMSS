"""
Uncertainty Engine Views

Endpoints for:
- Macro snapshots (CBN/NBS parameters) — CRUD + fetch current
- Cash Flow at Risk (Monte Carlo simulation)
- Stress testing
- Macro regime classification
- Real cost of borrowing calculator
"""

from django.http import JsonResponse
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from .helpers_uncertainty import (
    cash_flow_at_risk,
    stress_test_business,
    classify_macro_regime,
    compute_real_cost_of_borrowing,
    get_macro_parameters,
)
from .models_uncertainty import MacroSnapshot, ScenarioForecast, MacroDataLog
from .permissions import IsOwnerAdminManagerOrReadonly, IsOwnerOrAdmin
from .serializers_uncertainty import (
    MacroSnapshotSerializer, MacroSnapshotSummarySerializer,
    ScenarioForecastSerializer, MacroDataLogSerializer,
    CFaRInputSerializer, RealCostInputSerializer,
)


class MacroSnapshotViewSet(viewsets.ModelViewSet):
    """
    Manage Nigerian macro-economic snapshots.

    - GET /macro/ — list all snapshots
    - GET /macro/current/ — get the active snapshot
    - POST /macro/ — create a new snapshot (marks it as current)
    - GET /macro/fetch-log/ — view data fetch history
    """
    queryset = MacroSnapshot.objects.all()
    serializer_class = MacroSnapshotSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_serializer_class(self):
        if self.action == 'list':
            return MacroSnapshotSummarySerializer
        return MacroSnapshotSerializer

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """Get the currently active macro snapshot."""
        snapshot = MacroSnapshot.get_current()
        if not snapshot:
            return JsonResponse(
                {
                    "error": "No macro snapshot available. "
                    "Create one manually or run: "
                    "python manage.py fetch_macro_data"
                },
                status=404,
            )

        serializer = MacroSnapshotSerializer(snapshot)
        regime = classify_macro_regime()

        return JsonResponse({
            'snapshot': serializer.data,
            'regime': regime,
        })

    @action(detail=False, methods=['get'], url_path='fetch-log')
    def fetch_log(self, request):
        """View the history of macro data fetch operations."""
        logs = MacroDataLog.objects.all()[:20]
        serializer = MacroDataLogSerializer(logs, many=True)
        return Response(serializer.data)


class UncertaintyEngineViewSet(viewsets.ViewSet):
    """
    Core Uncertainty Engine endpoints.

    - POST /uncertainty/cash-flow-at-risk/ — run Monte Carlo CFaR simulation
    - GET /uncertainty/stress-test/ — stress test the business
    - GET /uncertainty/regime/ — current macro regime classification
    - POST /uncertainty/real-cost/ — compute real cost of borrowing
    """
    permission_classes = [IsOwnerOrAdmin]

    def get_business(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    @action(detail=False, methods=['post'], url_path='cash-flow-at-risk')
    def cfar(self, request):
        """
        Run a Monte Carlo Cash Flow at Risk simulation.

        Simulates future cash flows under macro uncertainty and returns
        percentile-based risk measures.
        """
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        serializer = CFaRInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            results = cash_flow_at_risk(
                business,
                horizon_months=serializer.validated_data['horizon_months'],
                num_simulations=serializer.validated_data['num_simulations'],
                confidence_level=serializer.validated_data['confidence_level'],
            )
        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=400)

        # Save forecast
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        macro_snapshot = MacroSnapshot.get_current()

        ScenarioForecast.objects.create(
            business=business,
            forecast_type=ScenarioForecast.ForecastType.CASH_FLOW,
            macro_snapshot=macro_snapshot,
            base_case=results['scenarios']['base_case'],
            optimistic_case=results['scenarios']['optimistic'],
            pessimistic_case=results['scenarios']['pessimistic'],
            stress_case=results['scenarios']['stress'],
            mean_value=results['mean_cash_flow'],
            std_deviation=results['std_deviation'],
            confidence_interval_lower=results['percentiles']['p5'],
            confidence_interval_upper=results['percentiles']['p95'],
            confidence_level=serializer.validated_data['confidence_level'] * 100,
            num_simulations=serializer.validated_data['num_simulations'],
            forecast_horizon_months=serializer.validated_data['horizon_months'],
            parameters_json=serializer.validated_data,
            results_json=results,
            user=user,
        )

        return JsonResponse(results)

    @action(detail=False, methods=['get'], url_path='stress-test')
    def stress_test(self, request):
        """
        Stress test the business under adverse macro conditions.

        Runs 4 default stress scenarios:
        1. Inflation spike (+10%)
        2. Revenue collapse (-30%)
        3. Combined macro shock
        4. Interest rate shock (+5%)
        """
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        try:
            results = stress_test_business(business)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

        return JsonResponse(results)

    @action(detail=False, methods=['get'], url_path='regime')
    def regime(self, request):
        """
        Classify the current Nigerian macro environment.

        Returns: STABLE, ELEVATED, or CRISIS with explanation.
        """
        regime = classify_macro_regime()
        return JsonResponse(regime)

    @action(detail=False, methods=['post'], url_path='real-cost')
    def real_cost(self, request):
        """
        Calculate the real cost of borrowing using the Fisher equation.

        At 32% nominal rate with 33% inflation, the real cost is negative.
        This is a critical insight for Nigerian business loan decisions.
        """
        serializer = RealCostInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = compute_real_cost_of_borrowing(
            nominal_rate=serializer.validated_data['nominal_rate'],
            inflation_rate=serializer.validated_data.get('inflation_rate'),
        )

        return JsonResponse(result)

    @action(detail=False, methods=['get'], url_path='forecasts')
    def forecast_history(self, request):
        """List recent scenario forecasts for this business."""
        business = self.get_business()
        if not business:
            return JsonResponse(
                {"error": "User has no associated business."}, status=400
            )

        forecasts = ScenarioForecast.objects.filter(
            business=business
        )[:20]
        serializer = ScenarioForecastSerializer(forecasts, many=True)
        return Response(serializer.data)
