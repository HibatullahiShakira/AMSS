from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncomeViewSet, ExpenseViewSet, AssetViewSet, AssetProjectSimulation

router = DefaultRouter()
router.register(r'incomes', IncomeViewSet, basename='income')
router.register(r'expenses', ExpenseViewSet, basename='expense')
router.register(r'assets', AssetViewSet, basename='assets')
router.register(r'asset_project_simulation', AssetProjectSimulation, basename='asset_project_simulation')
urlpatterns = [
    path('', include(router.urls)),
]
