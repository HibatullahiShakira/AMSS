from rest_framework import serializers

from .helper import generate_income_statement
from .models import Income, Expense, Transaction, Asset, Liability, Equity, Budget, Business
from django.utils import timezone


def validate_positive(value):
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return value


def validate_date(value):
    if value > timezone.now().date():
        raise serializers.ValidationError("Date cannot be in the future.")
    return value


class BusinessAwareSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        business = Business.objects.get(user=user)
        validated_data['business'] = business
        return super().create(validated_data)


class IncomeSerializer(BusinessAwareSerializer):
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
            raise serializers.ValidationError(
                "Income with the same date, source, and description already exists for this user.")
        return super().validate(attrs)

    def validate_date(self, value):
        return validate_date(value)


class ExpenseSerializer(BusinessAwareSerializer):
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


class TransactionSerializer(BusinessAwareSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'


class AssetSerializer(BusinessAwareSerializer):
    class Meta:
        model = Asset
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)

    def validate_useful_life(self, value):
        if value <= 0:
            raise serializers.ValidationError("Useful life must be greater than zero.")
        return value


class LiabilitySerializer(BusinessAwareSerializer):
    class Meta:
        model = Liability
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)


class EquitySerializer(BusinessAwareSerializer):
    class Meta:
        model = Equity
        fields = '__all__'

    def validate_amount(self, value):
        return validate_positive(value)


class BudgetSerializer(BusinessAwareSerializer):
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


class GenerateIncomeStatementSerializer(BusinessAwareSerializer):
    year = serializers.IntegerField(required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    period = serializers.ChoiceField(choices=['monthly', 'quarterly', 'yearly'], default='monthly')
    currency = serializers.CharField(required=False)


class IncomeStatementChartSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=['D', 'M', 'Y'], default='M')

    def get_income_data(self, business):
        income_records = Income.objects.filter(business=business)
        return [{'date': record.date, 'source': record.source, 'amount': record.amount} for record in income_records]

    def get_expense_data(self, business):
        expense_records = Expense.objects.filter(business=business)
        return [{'date': record.date, 'category': record.expense_category, 'amount': record.amount} for record in expense_records]

    def to_representation(self, instance):
        business_id = self.context['request'].user.business.id
        period = self.validated_data.get('period', 'M')

        income_data = self.get_income_data(business_id)
        expense_data = self.get_expense_data(business_id)

        analysis_result = generate_income_statement(income_data, expense_data, period)

        return {
            'income_data': analysis_result['income_data'],
            'expense_data': analysis_result['expense_data'],
            'income_time_series': analysis_result['income_time_series'],
            'expense_time_series': analysis_result['expense_time_series']
        }
