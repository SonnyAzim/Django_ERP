"""
Valuation Serializers
"""
from rest_framework import serializers
from .models import StockValuation, ValuationSummary, CategoryValue


class StockValuationSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = StockValuation
        fields = [
            'id', 'item', 'item_name', 'item_sku',
            'current_value', 'local_value', 'foreign_value',
            'calculated_at'
        ]


class CategoryValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryValue
        fields = ['id', 'major_category', 'total_value', 'percentage', 'item_count', 'calculated_at']


class ValuationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ValuationSummary
        fields = [
            'id', 'total_value', 'local_value', 'foreign_value',
            'total_items', 'calculated_at'
        ]
