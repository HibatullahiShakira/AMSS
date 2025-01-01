from rest_framework.routers import DefaultRouter
from .views import IncomeStatementChartViewSet

router = DefaultRouter()

router.register('income_expense_chart_analysis', IncomeStatementChartViewSet, 'income_chart_analysis')
urlpatterns = router.urls


