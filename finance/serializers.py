from datetime import timedelta
from decimal import Decimal

from rest_framework import serializers

from .helpers import generate_payment_schedule
from .models import Income, Business, Expense, Asset, Liability, PaymentSchedule, Creditor, Collateral, \
    PaymentInstallment, Customer, Supplier, AccountsReceivable, AccountsPayable, CashFlowForecast
from users.models import User
from rest_framework_simplejwt.models import TokenUser


def validate_positive(value):
    if value <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return value


class BusinessAwareSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id)
        print(f"Resolved User from TokenUser: {user}")

        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['user'] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id)
        print(f"Resolved User from TokenUser: {user}")

        business = getattr(user, 'business', None)
        if business is None:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['user'] = user
        return super().update(instance, validated_data)


class IncomeSerializer(BusinessAwareSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    business = serializers.HiddenField(default=serializers.CurrentUserDefault())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive])

    class Meta:
        model = Income
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id)
        print(f"Resolved User from TokenUser: {user}")

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        attrs['business'] = business
        attrs['user'] = user

        source = attrs.get('source')
        description = attrs.get('description')

        if source and description:
            existing_income = Income.objects.filter(
                user=user,
                business=business,
                source=source,
                description=description
            ).exists()

            if existing_income:
                raise serializers.ValidationError(
                    "Income with the same source and description already exists for this user.")
        return super().validate(attrs)


class ExpenseSerializer(BusinessAwareSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    business = serializers.HiddenField(default=serializers.CurrentUserDefault())
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, validators=[validate_positive])

    class Meta:
        model = Expense
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id)
        print(f"Resolved User from TokenUser: {user}")

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        attrs['business'] = business
        attrs['user'] = user

        expense_category = attrs.get('expense_category')
        description = attrs.get('description')

        if expense_category and description:
            existing_expense = Expense.objects.filter(
                user=user,
                business=business,
                expense_category=expense_category,
                description=description
            ).exists()

            if existing_expense:
                raise serializers.ValidationError(
                    "Expense with the same category and description already exists for this user.")
        return super().validate(attrs)


class AssetListSerializer(BusinessAwareSerializer):
    class Meta:
        model = Asset
        fields = ['id', 'user', 'name', 'description', 'amount', 'date_acquired', 'asset_types', 'business']


class AssetDetailSerializer(BusinessAwareSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    business = serializers.HiddenField(default=serializers.CurrentUserDefault())
    amount = serializers.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        model = Asset
        fields = '__all__'

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user if not isinstance(request.user, TokenUser) else User.objects.get(id=request.user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        attrs['business'] = business
        attrs['user'] = user

        name = attrs.get('name')
        description = attrs.get('description')

        if name and description:
            existing_asset = Asset.objects.filter(
                user=user,
                business=business,
                name=name,
                description=description
            ).exists()

            if existing_asset:
                raise serializers.ValidationError(
                    "Asset with the same name and description already exists for this user.")
        return attrs


class ScenarioSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    mean_value = serializers.FloatField()
    std_dev = serializers.FloatField()
    percentile_25 = serializers.FloatField()
    percentile_75 = serializers.FloatField()
    percentile_5 = serializers.FloatField()
    percentile_95 = serializers.FloatField()
    best_case = serializers.FloatField()
    worst_case = serializers.FloatField()
    most_likely = serializers.FloatField()


class RiskToleranceSerializer(serializers.Serializer):
    risk_tolerance = serializers.ChoiceField(choices=['low', 'moderate', 'high'], default='moderate')


class ExplainScenarioSerializer(serializers.Serializer):
    year = serializers.IntegerField()
    explanation = serializers.CharField()


class StorySerializer(serializers.Serializer):
    year = serializers.IntegerField()
    story = serializers.CharField()


class ScenarioQueryParamsSerializer(serializers.Serializer):
    year = serializers.IntegerField(default=1, min_value=1, max_value=5)
    risk_tolerance = serializers.ChoiceField(choices=['low', 'moderate', 'high'], default='moderate')


class LiabilitySerializer(BusinessAwareSerializer):
    class Meta:
        model = Liability
        fields = '__all__'


class PaymentScheduleSerializer(BusinessAwareSerializer):
    def update(self, instance, validated_data):
        installment_amount = validated_data.get('installment_amount')
        instance.installment_amount = installment_amount

        liability = instance.liability
        liability.paid_amount += Decimal(installment_amount)
        liability.save()

        instance.save()
        return instance

    class Meta:
        model = PaymentSchedule
        fields = '__all__'


class CreditorSerializer(BusinessAwareSerializer):
    class Meta:
        model = Creditor
        fields = '__all__'


class CollateralSerializer(BusinessAwareSerializer):
    class Meta:
        model = Collateral
        fields = '__all__'


class GeneratePaymentScheduleSerializer(serializers.Serializer):
    principal = serializers.DecimalField(max_digits=20, decimal_places=2)
    interest_rate = serializers.DecimalField(max_digits=10, decimal_places=2)
    term_years = serializers.IntegerField()
    payment_frequency = serializers.ChoiceField(choices=[
        ('Weekly', 'Weekly'),
        ('Bi-Weekly', 'Bi-Weekly'),
        ('Monthly', 'Monthly'),
        ('Quarterly', 'Quarterly'),
        ('Semi-Annually', 'Semi-Annually'),
        ('Annually', 'Annually'),
    ])
    start_date = serializers.DateField()
    liability_name = serializers.CharField(max_length=50)

    def create(self, validated_data):
        principal = validated_data['principal']
        interest_rate = validated_data['interest_rate']
        term_years = validated_data['term_years']
        payment_frequency = validated_data['payment_frequency']
        start_date = validated_data['start_date']
        user = self.context['request'].user

        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        name = validated_data['liability_name']

        print(f"user: {user}")
        print(f"name: {name}")
        print(f"business: {user.business}")

        # Check if user has an associated business
        if not user.business:
            raise serializers.ValidationError("User has no associated business.")

        payments = generate_payment_schedule(principal, interest_rate, term_years, payment_frequency, start_date)

        liability, created = Liability.objects.get_or_create(
            user=user,
            name=name,
            defaults={
                'amount': principal,
                'interest_rate': interest_rate,
                'liability_type': 'Current',
                'business': user.business,
                'date_incurred': start_date,
                'due_date': start_date + timedelta(days=term_years * 365),
                'paid_amount': Decimal('0.00')
            }
        )

        print(f"liability: {liability}, created: {created}")

        payment_schedule = PaymentSchedule.objects.create(
            liability=liability,
            payment_frequency=payment_frequency,
            start_date=start_date,
            end_date=start_date + timedelta(days=term_years * 365),
            business=user.business,
            user=user
        )

        print(f"payment_schedule: {payment_schedule}")

        payment_installments = []
        for payment in payments:
            payment_installment = PaymentInstallment(
                schedule=payment_schedule,
                date=payment['date'],
                principal=payment['principal'],
                interest=payment['interest'],
                remaining_principal=payment['remaining_principal']
            )
            payment_installments.append(payment_installment)

        PaymentInstallment.objects.bulk_create(payment_installments)

        # Prepare JSON serializable response
        installments_data = [
            {
                'date': installment.date,
                'principal': str(installment.principal),
                'interest': str(installment.interest),
                'remaining_principal': str(installment.remaining_principal)
            } for installment in payment_installments
        ]

        response_data = {
            "schedule": {
                'id': payment_schedule.id,
                'liability': payment_schedule.liability.id,
                'payment_frequency': payment_schedule.payment_frequency,
                'start_date': payment_schedule.start_date,
                'end_date': payment_schedule.end_date,
                'business': payment_schedule.business.id,
                'user': payment_schedule.user.id
            },
            "installments": installments_data
        }

        return response_data


class CustomerSerializer(BusinessAwareSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class SupplierSerializer(BusinessAwareSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'


class AccountsReceivableSerializer(BusinessAwareSerializer):
    class Meta:
        model = AccountsReceivable
        fields = '__all__'


class AccountsPayableSerializer(BusinessAwareSerializer):
    class Meta:
        model = AccountsPayable
        fields = '__all__'


class CashFlowForecastSerializer(BusinessAwareSerializer):
    class Meta:
        model = CashFlowForecast
        fields = '__all__'


class ProjectionInputSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=['daily', 'weekly', 'bi-weekly', 'monthly', 'quarterly', 'yearly'],
                                     default='monthly')
    forecast_steps = serializers.IntegerField(min_value=1, default=12)
    seasonal_period = serializers.IntegerField(min_value=1, default=12)


class PendingPaymentSummaryForPeriodSerializer(serializers.Serializer):
    total_pending_receivables_for_period = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_pending_payable_for_period = serializers.DecimalField(max_digits=20, decimal_places=2)
    remaining_balance_for_period = serializers.DecimalField(max_digits=20, decimal_places=2)


class PendingPaymentSummarySerializer(serializers.Serializer):
    total_pending_receivables = serializers.DecimalField(max_digits=20, decimal_places=2)
    total_pending_payable = serializers.DecimalField(max_digits=20, decimal_places=2)
    remaining_balance = serializers.DecimalField(max_digits=20, decimal_places=2)


class DateRangeSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True, format='%Y-%m-%d')
    end_date = serializers.DateField(required=True, format='%Y-%m-%d')


class PeriodSerializer(serializers.Serializer):
    period = serializers.ChoiceField(choices=['daily', 'monthly', 'quarterly', 'yearly'], required=True)


class RealTimeMonitoringSerializer(serializers.Serializer):
    threshold = serializers.IntegerField(required=True)



