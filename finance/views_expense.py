"""
Expense & Reminder Engine — Views

Endpoints:
- /finance/expense-categories/     — CRUD for expense categories
- /finance/recurring-expenses/     — CRUD for recurring expenses
- /finance/reminders/              — List, acknowledge, snooze reminders
- /finance/expense-intelligence/   — Anomaly detection, spending analysis
"""

from datetime import date, timedelta
from django.db import models
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .views import BusinessOwnerViewSet
from .models_expense import ExpenseCategory, RecurringExpense, Reminder, ReminderLog
from .serializers_expense import (
    ExpenseCategorySerializer,
    RecurringExpenseSerializer,
    ReminderSerializer,
    ReminderAcknowledgeSerializer,
)
from .helpers_expense import (
    generate_smart_reminders,
    detect_expense_anomalies,
    get_expense_breakdown,
    compute_materiality_score,
    compute_coverage_ratio,
    determine_urgency_level,
)
from .permissions import IsOwnerOrAdmin


class ExpenseCategoryViewSet(BusinessOwnerViewSet):
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    permission_classes = [IsOwnerOrAdmin]


class RecurringExpenseViewSet(BusinessOwnerViewSet):
    queryset = RecurringExpense.objects.all()
    serializer_class = RecurringExpenseSerializer
    permission_classes = [IsOwnerOrAdmin]

    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        """
        Mark a recurring expense as paid for the current period.
        Advances next_due_date to the next period.
        """
        recurring = self.get_object()
        recurring.total_paid += recurring.amount
        recurring.payment_count += 1

        # Advance next_due_date based on frequency
        freq_days = {
            'DAILY': 1, 'WEEKLY': 7, 'BIWEEKLY': 14,
            'MONTHLY': 30, 'QUARTERLY': 90,
            'SEMI_ANNUALLY': 182, 'ANNUALLY': 365,
        }
        days = freq_days.get(recurring.frequency, 30)
        recurring.next_due_date = recurring.next_due_date + timedelta(days=days)

        # Check if end_date reached
        if recurring.end_date and recurring.next_due_date > recurring.end_date:
            recurring.status = 'COMPLETED'

        recurring.save()

        return JsonResponse({
            'message': f'{recurring.name} marked as paid.',
            'next_due_date': str(recurring.next_due_date),
            'total_paid': float(recurring.total_paid),
            'payment_count': recurring.payment_count,
        })


class ReminderViewSet(BusinessOwnerViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
    permission_classes = [IsOwnerOrAdmin]

    def get_queryset(self):
        """Filter by status and urgency if query params provided."""
        qs = super().get_queryset()
        status_filter = self.request.query_params.get('status')
        urgency_filter = self.request.query_params.get('urgency')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if urgency_filter:
            qs = qs.filter(urgency_level=urgency_filter)
        return qs

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_reminders(self, request):
        """
        Scan all upcoming obligations and generate smart reminders.
        Computes materiality, coverage ratio, and urgency for each.
        """
        business = self.get_business()
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        reminders = generate_smart_reminders(business)
        serializer = ReminderSerializer(reminders, many=True)
        return JsonResponse({
            'message': f'Generated/updated {len(reminders)} reminders.',
            'reminders': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='acknowledge')
    def acknowledge_reminder(self, request, pk=None):
        """Acknowledge or snooze a reminder."""
        reminder = self.get_object()
        serializer = ReminderAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action_type = serializer.validated_data['action']

        if action_type == 'acknowledge':
            reminder.status = 'ACKNOWLEDGED'
            reminder.save()
            ReminderLog.objects.create(
                reminder=reminder,
                action='ACKNOWLEDGED',
                channel='IN_APP',
                message='Reminder acknowledged by user.',
                performed_by=request.user if not hasattr(request.user, 'token_type') else None
            )
            return JsonResponse({'message': 'Reminder acknowledged.'})

        elif action_type == 'snooze':
            snooze_days = serializer.validated_data.get('snooze_days', 1)
            reminder.status = 'SNOOZED'
            reminder.snooze_until = timezone.now() + timedelta(days=snooze_days)
            reminder.save()
            ReminderLog.objects.create(
                reminder=reminder,
                action='SNOOZED',
                channel='IN_APP',
                message=f'Reminder snoozed for {snooze_days} day(s).',
                performed_by=request.user if not hasattr(request.user, 'token_type') else None
            )
            return JsonResponse({'message': f'Reminder snoozed for {snooze_days} day(s).'})

    @action(detail=False, methods=['get'], url_path='summary')
    def reminder_summary(self, request):
        """Get a summary of all reminders by urgency and status."""
        business = self.get_business()
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        qs = Reminder.objects.filter(business=business)
        summary = {
            'total': qs.count(),
            'by_urgency': {
                'critical': qs.filter(urgency_level='CRITICAL').count(),
                'urgent': qs.filter(urgency_level='URGENT').count(),
                'normal': qs.filter(urgency_level='NORMAL').count(),
                'low': qs.filter(urgency_level='LOW').count(),
            },
            'by_status': {
                'pending': qs.filter(status='PENDING').count(),
                'sent': qs.filter(status='SENT').count(),
                'acknowledged': qs.filter(status='ACKNOWLEDGED').count(),
                'overdue': qs.filter(status='OVERDUE').count(),
            },
            'total_upcoming_obligations': float(
                qs.filter(status__in=['PENDING', 'SENT']).aggregate(
                    total=models.Sum('amount')
                )['total'] or 0
            ),
        }
        return JsonResponse(summary)


class ExpenseIntelligenceViewSet(viewsets.ViewSet):
    """Analytics and intelligence endpoints for expenses."""
    permission_classes = [IsOwnerOrAdmin]

    def _get_business(self, request):
        from users.models import User
        from rest_framework_simplejwt.models import TokenUser
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)
        return getattr(user, 'business', None)

    @action(detail=False, methods=['get'], url_path='anomalies')
    def anomalies(self, request):
        """Detect expense anomalies against historical norms."""
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        anomalies = detect_expense_anomalies(business)
        return JsonResponse({
            'anomaly_count': len(anomalies),
            'anomalies': anomalies
        })

    @action(detail=False, methods=['get'], url_path='breakdown')
    def breakdown(self, request):
        """Get expense breakdown by category."""
        business = self._get_business(request)
        if not business:
            return JsonResponse({'error': 'No business found.'}, status=400)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        result = get_expense_breakdown(business, start_date, end_date)
        return JsonResponse(result)
