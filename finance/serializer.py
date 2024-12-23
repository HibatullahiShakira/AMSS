from rest_framework import serializers
from .models import Income, Expense, Transaction, Asset, Liability, Equity, Budget
from django.utils import timezone


def validate_positive(value):
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return value


def validate_date(value):
    if value > timezone.now().date():
        raise serializers.ValidationError("Date cannot be in the future.")
    return value


class IncomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Income
        fields = '__all__'

    def validate(self, attrs):
        existing_income = Income.objects.filter(
            user=self.context['request'].user,
            date=attrs['date'],
            source=attrs['source'],
            description=attrs['description']
        ).exists()
        if existing_income:
            raise serializers.ValidationError("Income with the same date, source, and description already exists for "
                                              "this user.")
        return super().validate(attrs)

    def validate_date(self, value):
        return validate_date(value)


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'

    def validate(self, attrs):
        existing_expense = Expense.objects.filter(
            user=self.context['request'].user,
            date=attrs['date'],
            expense_category=attrs['expense_category'],
            description=attrs['description']
        ).exists()
        if existing_expense:
            raise serializers.ValidationError(
                "Expense with the same date, category, and description already exists for this user.")
        return super().validate(attrs)

    def validate_date(self, value):
        return validate_date(value)


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)

    def validate_useful_life(self, value):
        if value <= 0:
            raise serializers.ValidationError("Useful life must be greater than zero.")
        return value


class LiabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Liability
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)


class EquitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Equity
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)


class BudgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Budget
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)

    def validate_start_date(self, value):
        return validate_date(value)

    def validate_end_date(self, value):
        start_date = self.initial_data.get('start_date') if self.instance is None else self.instance.start_date
        if value < start_date:
            raise serializers.ValidationError("End date must be after the start date.")
        return value

