"""
Asset Tracker — Enhanced Serializers
"""

from rest_framework import serializers
from rest_framework_simplejwt.models import TokenUser

from users.models import User
from .models_asset import AssetMaintenanceLog, AssetDisposal, DepreciationSchedule


class AssetMaintenanceLogSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = AssetMaintenanceLog
        fields = [
            'id', 'asset', 'asset_name', 'date', 'maintenance_type',
            'description', 'cost', 'performed_by', 'vendor',
            'next_maintenance_due', 'notes', 'user', 'created_at',
        ]
        read_only_fields = ['user', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['user'] = user
        return super().create(validated_data)


class AssetDisposalSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = AssetDisposal
        fields = [
            'id', 'asset', 'asset_name', 'date', 'method',
            'proceeds', 'book_value_at_disposal', 'gain_or_loss',
            'buyer', 'reason', 'disposal_costs', 'user', 'created_at',
        ]
        read_only_fields = ['gain_or_loss', 'user', 'created_at']

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user
        if isinstance(user, TokenUser):
            user = User.objects.get(id=user.id)

        business = getattr(user, 'business', None)
        if not business:
            raise serializers.ValidationError("User has no associated business.")

        validated_data['business'] = business
        validated_data['user'] = user
        return super().create(validated_data)


class DepreciationScheduleSerializer(serializers.ModelSerializer):
    asset_name = serializers.CharField(source='asset.name', read_only=True)

    class Meta:
        model = DepreciationSchedule
        fields = [
            'id', 'asset', 'asset_name', 'period_number',
            'period_start_date', 'period_end_date',
            'opening_book_value', 'depreciation_amount',
            'accumulated_depreciation', 'closing_book_value',
            'is_posted', 'journal_entry', 'created_at',
        ]
        read_only_fields = ['created_at']
