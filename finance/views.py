from datetime import datetime

from django.http import Http404, JsonResponse
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework_simplejwt.models import TokenUser
import pandas as pd
from users.models import User
from .helpers import generate_asset_project_simulations, get_comprehensive_breakdown, explain_scenario_keys, \
    generate_asset_report, calculate_total_liabilities, calculate_total_assets, calculate_interest_accrual, \
    track_loan_payments, perform_projection, calculate_remaining_balance, \
    calculate_remaining_balance_for_period, generate_report_based_on_period, generate_report_based_on_date_range, \
    calculate_real_time_data, perform_cash_outflow_projection
from .models import Income, Expense, Asset, Liability, PaymentSchedule, Creditor, Collateral, Customer, Supplier, \
    AccountsReceivable, AccountsPayable
from .serializers import IncomeSerializer, ExpenseSerializer, AssetListSerializer, AssetDetailSerializer, \
    ScenarioSerializer, RiskToleranceSerializer, StorySerializer, ExplainScenarioSerializer, \
    ScenarioQueryParamsSerializer, LiabilitySerializer, PaymentScheduleSerializer, CreditorSerializer, \
    CollateralSerializer, GeneratePaymentScheduleSerializer, CustomerSerializer, SupplierSerializer, \
    ProjectionInputSerializer, PendingPaymentSummaryForPeriodSerializer, PendingPaymentSummarySerializer, \
    DateRangeSerializer, PeriodSerializer, RealTimeMonitoringSerializer
from .permissions import IsOwnerAdminManagerOrReadonly, IsOwnerOrAdmin


class BusinessOwnerViewSet(viewsets.ModelViewSet):
    def get_business(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            return None

        return business

    def get_queryset(self):
        business = self.get_business()
        if business is None:
            return self.queryset.none()

        return self.queryset.filter(business_id=business.id)

    def perform_create(self, serializer):
        business = self.get_business()
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        serializer.save(business=business)

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, self.get_object())
        business = self.get_business()
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        serializer.save(business=business)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, self.get_object())
        business = self.get_business()
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        instance.delete()


class IncomeViewSet(BusinessOwnerViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_object(self):
        business = self.get_business()
        income_id = self.kwargs.get('pk')

        if business:
            try:
                income = Income.objects.get(business=business, id=income_id)
                return income
            except Income.DoesNotExist:
                raise Http404("No Income matches the given query.")

        raise Http404("No Income matches the given query.")


class ExpenseViewSet(BusinessOwnerViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_object(self):
        business = self.get_business()
        expense_id = self.kwargs.get('pk')

        if business:
            try:
                expense = Expense.objects.get(business=business, id=expense_id)
                return expense
            except Expense.DoesNotExist:
                raise Http404("No expense matches the given query.")

        raise Http404("No expense matches the given query.")


class AssetViewSet(BusinessOwnerViewSet):
    queryset = Asset.objects.all()
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        business = self.get_business()
        asset_id = self.kwargs.get('pk')

        if business:
            try:
                asset = Asset.objects.get(business=business, id=asset_id)
                return asset
            except Asset.DoesNotExist:
                raise Http404("No asset matches the given query.")

        raise Http404("No asset matches the given query.")

    def get_serializer_class(self):
        if self.action == 'list':
            return AssetListSerializer
        return AssetDetailSerializer

    @action(detail=True, methods=['get'])
    def depreciation(self, request, pk=None):
        asset = self.get_object()
        depreciation_value = asset.depreciation_rate
        return JsonResponse({'depreciation_value': depreciation_value})

    @action(detail=True, methods=['get'])
    def appreciation(self, request, pk=None):
        asset = self.get_object()
        appreciation_value = asset.appreciation_rate
        return JsonResponse({'appreciation_value': appreciation_value})

    @action(detail=False, methods=['get'], url_path='total-assets')
    def total_assets(self, request):
        business = self.get_business()

        if business is None:
            return JsonResponse({"error": "User has no associated business."}, status=400)

        assets = Asset.objects.filter(business=business)
        total = calculate_total_assets(assets)

        return JsonResponse({"total_assets": total})


class AssetProjectSimulation(viewsets.ViewSet):
    permission_classes = [IsOwnerOrAdmin]

    def get_asset(self, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            raise Http404("No asset matches the given query.")
        return asset

    @action(detail=True, methods=['get'])
    def asset_analysis(self, request, pk=None):
        asset = self.get_asset(pk)
        risk_tolerance_serializer = RiskToleranceSerializer(data=request.query_params)
        risk_tolerance_serializer.is_valid(raise_exception=True)
        risk_tolerance = risk_tolerance_serializer.validated_data['risk_tolerance']
        scenarios = generate_asset_project_simulations(asset, risk_tolerance=risk_tolerance)
        serializer = ScenarioSerializer(scenarios, many=True)
        return JsonResponse(serializer.data, safe=False)

    @action(detail=True, methods=['get'])
    def comprehensive_breakdown(self, request, pk=None):
        asset = self.get_asset(pk)
        breakdown = get_comprehensive_breakdown(asset)
        return JsonResponse(breakdown)

    @action(detail=True, methods=['get'])
    def explain_scenario(self, request, pk=None):
        asset = self.get_asset(pk)
        year = int(request.query_params.get('year', 1))
        scenarios = generate_asset_project_simulations(asset)
        explanation = explain_scenario_keys(asset, year, scenarios)
        serializer = ExplainScenarioSerializer({'year': year, 'explanation': explanation})
        return JsonResponse(serializer.data)

    @action(detail=True, methods=['get'])
    def generate_asset_report(self, request, pk=None):
        asset = self.get_asset(pk)
        params_serializer = ScenarioQueryParamsSerializer(data=request.query_params)
        params_serializer.is_valid(raise_exception=True)
        year = params_serializer.validated_data['year']
        risk_tolerance = params_serializer.validated_data['risk_tolerance']
        scenarios = generate_asset_project_simulations(asset, risk_tolerance=risk_tolerance)
        story = generate_asset_report(asset, year, scenarios, risk_tolerance)
        serializer = StorySerializer({'year': year, 'story': story})
        return JsonResponse(serializer.data)


class LiabilityViewSet(BusinessOwnerViewSet):
    queryset = Liability.objects.all()
    serializer_class = LiabilitySerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        business = self.get_business()
        liability_id = self.kwargs.get('pk')

        if business:
            try:
                liability = Liability.objects.get(business=business, id=liability_id)
                return liability
            except Liability.DoesNotExist:
                raise Http404("No liability matches the given query.")

        raise Http404("No liability matches the given query.")

    @action(detail=False, methods=['get'], url_path='total-liabilities')
    def total_liabilities(self, request):
        user = request.user
        business = getattr(user, 'business', None)

        if business is None:
            return JsonResponse({"error": "User has no associated business."}, status=400)

        liabilities = Liability.objects.filter(business=business)
        total = calculate_total_liabilities(liabilities)

        return JsonResponse({"total_liabilities": total})

    @action(detail=True, methods=['get'], url_path='debt_management')
    def debt_management(self, request, pk=None):
        liability = self.get_object()

        interest_accrued = calculate_interest_accrual(liability)
        total_paid, remaining_balance = track_loan_payments(liability)

        payment_history = PaymentSchedule.objects.filter(liability=liability)
        payment_history_serializer = PaymentScheduleSerializer(payment_history, many=True)

        return JsonResponse({
            "liability": LiabilitySerializer(liability).data,
            "interest_accrued": interest_accrued,
            "total_paid": total_paid,
            "remaining_balance": remaining_balance,
            "payment_history": payment_history_serializer.data
        })


class PaymentScheduleViewSet(BusinessOwnerViewSet):
    queryset = PaymentSchedule.objects.all()
    serializer_class = GeneratePaymentScheduleSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        business = self.get_business()
        payment_schedule_id = self.kwargs.get('pk')

        if business:
            try:
                payment_schedule = PaymentSchedule.objects.get(business=business, id=payment_schedule_id)
                return payment_schedule
            except Expense.DoesNotExist:
                raise Http404("No payment schedule matches the given query.")

        raise Http404("No payment schedule matches the given query.")

    @action(detail=False, methods=['post'], url_path='generate-payment-schedule')
    def generate_payment_schedule(self, request):
        serializer = GeneratePaymentScheduleSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            payment_data = serializer.save()
            return JsonResponse({
                "message": "Payment schedule generated and saved successfully.",
                "payment_schedule": payment_data
            }, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreditorViewSet(BusinessOwnerViewSet):
    queryset = Creditor.objects.all()
    serializer_class = CreditorSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        business = self.get_business()
        creditor_id = self.kwargs.get('pk')

        if business:
            try:
                creditor = Creditor.objects.get(business=business, id=creditor_id)
                return creditor
            except Creditor.DoesNotExist:
                raise Http404("No creditor matches the given query.")

        raise Http404("No creditor matches the given query.")


class CollateralViewSet(BusinessOwnerViewSet):
    queryset = Collateral.objects.all()
    serializer_class = CollateralSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self):
        business = self.get_business()
        collateral_id = self.kwargs.get('pk')

        if business:
            try:
                collateral = Collateral.objects.get(business=business, id=collateral_id)
                return collateral
            except Collateral.DoesNotExist:
                raise Http404("No collateral matches the given query.")

        raise Http404("No collateral matches the given query.")


class CustomerViewSet(BusinessOwnerViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_object(self):
        business = self.get_business()
        customer_id = self.kwargs.get('pk')

        if business:
            try:
                collateral = Customer.objects.get(business=business, id=customer_id)
                return
            except Customer.DoesNotExist:
                raise Http404("No customer matches the given query.")

        raise Http404("No customer matches the given query.")


class SupplierViewSet(BusinessOwnerViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_object(self):
        business = self.get_business()
        supplier_id = self.kwargs.get('pk')

        if business:
            try:
                supplier = Supplier.objects.get(business=business, id=supplier_id)
                return supplier
            except Supplier.DoesNotExist:
                raise Http404("No supplier matches the given query.")

        raise Http404("No supplier matches the given query.")


class CashFlowOptimizationViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['get'])
    def pending_payments_summary(self, request):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            return JsonResponse({"error": "User has no associated business."}, status=400)

        date_serializer = DateRangeSerializer(data=request.data)
        if date_serializer.is_valid():
            start_date = date_serializer.validated_data['start_date']
            end_date = date_serializer.validated_data['end_date']
            print(f'start_date: {start_date}, end_date: {end_date}')
            total_pending_payments = calculate_remaining_balance_for_period(business, start_date, end_date)
            serializer = PendingPaymentSummaryForPeriodSerializer(total_pending_payments)
        else:
            print('Date range validation failed:', date_serializer.errors)
            total_pending_payments = calculate_remaining_balance(business)
            serializer = PendingPaymentSummarySerializer(total_pending_payments)

        return JsonResponse(serializer.data)

    @action(detail=False, methods=['get'])
    def strategies(self, request):
        strategies = [
            {
                "name": "Receivables Management",
                "recommendations": [
                    "Invoice promptly and follow up on overdue invoices.",
                    "Offer early payment discounts.",
                    "Implement strict credit control policies."
                ]
            },
            {
                "name": "Payables Management",
                "recommendations": [
                    "Take advantage of early payment discounts.",
                    "Negotiate better payment terms with suppliers.",
                    "Prioritize payments to avoid late fees."
                ]
            },
            {
                "name": "Cash Flow Forecasting",
                "recommendations": [
                    "Regularly update cash flow forecasts based on actual performance.",
                    "Adjust forecasts for seasonality and market trends.",
                    "Use predictive analytics to anticipate cash flow issues."
                ]
            },
            {
                "name": "Cash Reserve Management",
                "recommendations": [
                    "Maintain an adequate cash reserve for contingencies.",
                    "Allocate cash reserves based on risk tolerance and business needs.",
                    "Regularly review and adjust cash reserve levels."
                ]
            }
        ]
        return JsonResponse({"strategies": strategies})

    @action(detail=False, methods=['get'])
    def real_time_monitoring(self, request):
        serializer = RealTimeMonitoringSerializer(data=request.data)
        if serializer.is_valid():
            alert_threshold = serializer.validated_data['threshold']
            real_time_data, alerts = calculate_real_time_data(alert_threshold)

            return JsonResponse({
                "alerts": alerts
            })
        else:
            return JsonResponse(serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def date_range_report(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        date_serializer = DateRangeSerializer(data=request.data)
        if date_serializer.is_valid():
            start_date = date_serializer.validated_data.get('start_date')
            end_date = date_serializer.validated_data.get('end_date')
            try:
                start_date = datetime.strptime(str(start_date), '%Y-%m-%d').date()
                end_date = datetime.strptime(str(end_date), '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
            report = generate_report_based_on_date_range(business, start_date, end_date)
            return JsonResponse(report, safe=False)
        else:
            return JsonResponse(date_serializer.errors, status=400)

    @action(detail=False, methods=['get'])
    def all_records(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        report = generate_report_based_on_date_range(business)
        return JsonResponse(report, safe=False)


class CashFlowProjectionViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def projection(self, request):
        user = request.user
        serializer = ProjectionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        period = validated_data.get('period')
        forecast_steps = validated_data.get('forecast_steps')
        seasonal_period = validated_data.get('seasonal_period')

        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        results = perform_projection(business, period, forecast_steps, seasonal_period)

        return JsonResponse(results)

    @action(detail=False, methods=['get'])
    def perform_cash_outflow_projection(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        serializer = ProjectionInputSerializer(data=request.data)
        if serializer.is_valid():
            period = serializer.validated_data['period']
            forecast_steps = serializer.validated_data['forecast_steps']
            seasonal_period = serializer.validated_data['seasonal_period']

            projection = perform_cash_outflow_projection(business, period, forecast_steps, seasonal_period)
            return JsonResponse(projection, safe=False)
        else:
            return JsonResponse(serializer.errors, status=400)

