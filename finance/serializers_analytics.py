"""
Analytics & Reporting Engine — Serializers
"""

from rest_framework import serializers

class ReportRequestSerializer(serializers.Serializer):
    period = serializers.ChoiceField(
        choices=['MTD', 'YTD', 'CUSTOM'], 
        default='YTD',
        help_text="Time period for the report"
    )
    start_date = serializers.DateField(required=False, help_text="Required if period is CUSTOM")
    end_date = serializers.DateField(required=False, help_text="Required if period is CUSTOM")

    def validate(self, data):
        if data.get('period') == 'CUSTOM':
            if not data.get('start_date') or not data.get('end_date'):
                raise serializers.ValidationError("start_date and end_date are required for CUSTOM period.")
        return data
