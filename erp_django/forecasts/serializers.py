"""
Forecast Serializers
"""
from rest_framework import serializers
from .models import Forecast, MRPResult, Pipeline

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

class PipelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pipeline
        fields = [
            'id', 'item', 'sku', 'name', 'quantity', 'unit_price',
            'status', 'order_date', 'expected_date', 'received_date',
            'supplier', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Create pipeline item
        pipeline = Pipeline.objects.create(**validated_data)
        return pipeline
