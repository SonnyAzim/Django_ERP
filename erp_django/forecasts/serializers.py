"""
Forecast Serializers
"""
from rest_framework import serializers
from .models import Forecast, MRPResult


class ForecastSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = Forecast
        fields = [
            'id', 'item', 'item_name', 'item_sku',
            'month', 'quantity', 'created_at', 'updated_at'
        ]


class MRPResultSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = MRPResult
        fields = [
            'id', 'item', 'item_name', 'item_sku',
            'month', 'gross_requirement', 'projected_stock',
            'planned_order', 'safety_stock', 'calculated_at'
        ]


class ForecastUploadSerializer(serializers.Serializer):
    forecasts = serializers.ListField(
        child=serializers.DictField()
    )
