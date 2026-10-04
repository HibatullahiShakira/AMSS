"""
Analytics & Reporting Engine — Views

Endpoints:
- /finance/reports/pnl/          — Profit & Loss (Income Statement)
- /finance/reports/balance-sheet/— Balance Sheet
- /finance/reports/cash-flow/    — Cash Flow Statement
- /finance/reports/kpis/         — Financial KPIs
"""

from datetime import date
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from finance.permissions import IsOwnerOrAdmin
from .serializers_analytics import ReportRequestSerializer
from .helpers_analytics import (
    get_date_range,
    generate_profit_and_loss,
    generate_balance_sheet,
    generate_cash_flow,
    calculate_kpis
)


class ReportingViewSet(viewsets.ViewSet):
    """
    ViewSet for generating financial reports and analytics.
    """
    permission_classes = [IsOwnerOrAdmin]

    def _get_business(self, request):
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    @action(detail=False, methods=['post'], url_path='pnl')
    def profit_and_loss(self, request):
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        start_date, end_date = get_date_range(
            serializer.validated_data.get('period'),
            serializer.validated_data.get('start_date'),
            serializer.validated_data.get('end_date')
        )
        
        report = generate_profit_and_loss(business, start_date, end_date)
        return JsonResponse(report)

    @action(detail=False, methods=['post'], url_path='balance-sheet')
    def balance_sheet(self, request):
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        # Balance sheet is "as of" a specific date (usually end_date of the period)
        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        _, end_date = get_date_range(
            serializer.validated_data.get('period'),
            serializer.validated_data.get('start_date'),
            serializer.validated_data.get('end_date')
        )
        
        report = generate_balance_sheet(business, end_date)
        return JsonResponse(report)

    @action(detail=False, methods=['post'], url_path='cash-flow')
    def cash_flow(self, request):
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        serializer = ReportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        start_date, end_date = get_date_range(
            serializer.validated_data.get('period'),
            serializer.validated_data.get('start_date'),
            serializer.validated_data.get('end_date')
        )
        
        report = generate_cash_flow(business, start_date, end_date)
        return JsonResponse(report)

    @action(detail=False, methods=['get'], url_path='kpis')
    def kpis(self, request):
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)
            
        kpis = calculate_kpis(business)
        return JsonResponse(kpis)
