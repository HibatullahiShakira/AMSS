"""
Expense & Reminder Engine — Serializers
"""

from rest_framework import serializers
from .models_expense import ExpenseCategory, RecurringExpense, Reminder, ReminderLog


class ExpenseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseCategory
        fields = [
            'id', 'name', 'description', 'is_deductible',
            'macro_correlation', 'budget_limit_monthly', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class RecurringExpenseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = RecurringExpense
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'amount', 'currency', 'frequency', 'next_due_date',
            'start_date', 'end_date', 'auto_escalation_rate',
            'payee', 'status', 'total_paid', 'payment_count',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_paid', 'payment_count', 'created_at', 'updated_at']


class ReminderLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderLog
        fields = ['id', 'action', 'channel', 'message', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ReminderSerializer(serializers.ModelSerializer):
    logs = ReminderLogSerializer(many=True, read_only=True)
    days_until_due = serializers.SerializerMethodField()

    class Meta:
        model = Reminder
        fields = [
            'id', 'title', 'description', 'reminder_type', 'due_date',
            'amount', 'currency', 'materiality_score', 'coverage_ratio',
            'urgency_level', 'status', 'recurring_expense', 'liability',
            'snooze_until', 'escalation_count', 'days_until_due',
            'logs', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'materiality_score', 'coverage_ratio', 'urgency_level',
            'escalation_count', 'created_at', 'updated_at'
        ]

    def get_days_until_due(self, obj):
        from datetime import date
        delta = (obj.due_date - date.today()).days
        return delta


class ReminderAcknowledgeSerializer(serializers.Serializer):
    """Serializer for acknowledging or snoozing a reminder."""
    action = serializers.ChoiceField(choices=['acknowledge', 'snooze'])
    snooze_days = serializers.IntegerField(required=False, default=1, min_value=1, max_value=30)
