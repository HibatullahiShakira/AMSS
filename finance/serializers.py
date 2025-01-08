from decimal import Decimal

from rest_framework import serializers
from .models import Income, Business, Expense, Asset, Liability, PaymentSchedule, Creditor, Collateral
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
        fields = ['user', 'name', 'description', 'amount', 'date_acquired', 'asset_types', 'business']


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
