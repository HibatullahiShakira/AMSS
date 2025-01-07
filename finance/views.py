from django.http import Http404, JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from .helpers import generate_asset_project_simulations, get_comprehensive_breakdown, explain_scenario_keys
from .models import Income, Expense, Asset
from .serializers import IncomeSerializer, ExpenseSerializer, AssetListSerializer, AssetDetailSerializer, \
    ScenarioSerializer
from .permissions import IsOwnerAdminManagerOrReadonly, IsOwnerOrAdmin


class IncomeViewSet(viewsets.ModelViewSet):
    queryset = Income.objects.all()
    serializer_class = IncomeSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            return self.queryset.none()

        business_id = business.id
        return self.queryset.filter(business_id=business_id)

    def get_object(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        income_id = self.kwargs.get('pk')

        if business:
            try:
                income = Income.objects.get(business=business, id=income_id)
                return income
            except Income.DoesNotExist:
                raise Http404("No Income matches the given query.")

        raise Http404("No Income matches the given query.")

    def perform_create(self, serializer):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")
        serializer.save(user=user, business=business)

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")

        serializer.save(user=user, business=business)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        # if business is None:
        #     raise serializers.ValidationError("User has no associated business.")
        instance.delete()


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [IsOwnerAdminManagerOrReadonly]

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            return self.queryset.none()

        business_id = business.id
        return self.queryset.filter(business_id=business_id)

    def get_object(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        expense_id = self.kwargs.get('pk')

        if business:
            try:
                expense = Expense.objects.get(business=business, id=expense_id)
                return expense
            except Expense.DoesNotExist:
                raise Http404("No expense matches the given query.")

        raise Http404("No expense matches the given query.")

    def perform_create(self, serializer):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")
        serializer.save(user=user, business=business)

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")

        serializer.save(user=user, business=business)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        # if business is None:
        #     raise serializers.ValidationError("User has no associated business.")
        instance.delete()


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            return self.queryset.none()

        business_id = business.id
        return self.queryset.filter(business_id=business_id)

    def get_object(self):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
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

    def perform_create(self, serializer):
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")
        serializer.save(user=user, business=business)

    def perform_update(self, serializer):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if business is None:
            raise serializer.ValidationError("User has no associated business.")

        serializer.save(user=user, business=business)

    def perform_destroy(self, instance):
        self.check_object_permissions(self.request, self.get_object())
        user = self.request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        # if business is None:
        #     raise serializers.ValidationError("User has no associated business.")
        instance.delete()

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


class AssetProjectSimulation(viewsets.ViewSet):
    permission_classes = [IsOwnerOrAdmin]

    def get_asset(self, pk):
        try:
            asset = Asset.objects.get(pk=pk)
        except Asset.DoesNotExist:
            raise Http404("No asset matches the given query.")
        return asset

    @action(detail=True, methods=['get'])
    def scenario_analysis(self, request, pk=None):
        asset = self.get_asset(pk)
        risk_tolerance = request.query_params.get('risk_tolerance', 'moderate')
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
        return JsonResponse(explanation)
