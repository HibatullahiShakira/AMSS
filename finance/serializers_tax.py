"""
Nigerian Tax Engine — Serializers
"""

from rest_framework import serializers
from .models_tax import TaxConfiguration, TaxTransaction, TaxReturn, TaxFilingDeadline


class TaxConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxConfiguration
        fields = [
            'id', 'tin_number', 'is_vat_registered', 'vat_rate',
            'is_wht_agent', 'cit_rate', 'fiscal_year_end',
            'tax_office', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TaxTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxTransaction
        fields = [
            'id', 'transaction', 'tax_type', 'base_amount',
            'tax_amount', 'tax_rate', 'date', 'is_remitted',
            'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class TaxReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxReturn
        fields = [
            'id', 'tax_type', 'period_start', 'period_end',
            'total_liability', 'total_paid', 'status',
            'filing_date', 'firs_receipt_number', 'report_data_json',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_liability', 'report_data_json',
            'created_at', 'updated_at'
        ]


class TaxFilingDeadlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxFilingDeadline
        fields = [
            'id', 'tax_type', 'period_name', 'deadline_date',
            'is_filed', 'related_return', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
