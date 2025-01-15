from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncomeViewSet, ExpenseViewSet, AssetViewSet, AssetProjectSimulation, LiabilityViewSet, \
    PaymentScheduleViewSet, CollateralViewSet, CashFlowProjectionViewSet, CashFlowOptimizationViewSet

router = DefaultRouter()
router.register(r'incomes', IncomeViewSet, basename='income')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'assets', AssetViewSet, basename='assets')
router.register(r'asset_project_simulation', AssetProjectSimulation, basename='asset_project_simulation')
router.register(r'liabilities', LiabilityViewSet, basename='liabilities')
router.register(r'project_schedule', PaymentScheduleViewSet, basename='project_schedule')
router.register(r'collateral', CollateralViewSet, basename='collateral')
router.register(r'cash_projections', CashFlowProjectionViewSet, basename='cash_projections')
router.register(r'cash_flow', CashFlowOptimizationViewSet, basename='cash_flow')
urlpatterns = [
    path('', include(router.urls)),
]
