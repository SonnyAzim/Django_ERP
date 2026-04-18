"""
Duty Serializers
"""
from rest_framework import serializers
from .models import HSCode, ItemHSCode


class HSCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = HSCode
        fields = [
            'id', 'code', 'description', 'cd', 'rd', 'sd',
            'vat', 'ait', 'at', 'created_at'
        ]


class ItemHSCodeSerializer(serializers.ModelSerializer):
    hs_code_value = serializers.CharField(source='hs_code.code', read_only=True)
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = ItemHSCode
        fields = ['id', 'item', 'item_name', 'item_sku', 'hs_code', 'hs_code_value']


class DutyCalculationSerializer(serializers.Serializer):
    hs_code_id = serializers.IntegerField(required=False)
    hs_code = serializers.CharField(required=False)
    customs_value = serializers.DecimalField(max_digits=15, decimal_places=2)


class DutyCalculationResultSerializer(serializers.Serializer):
    hs_code = serializers.CharField()
    description = serializers.CharField()
    customs_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    cd = serializers.DecimalField(max_digits=15, decimal_places=2)
    rd = serializers.DecimalField(max_digits=15, decimal_places=2)
    sd = serializers.DecimalField(max_digits=15, decimal_places=2)
    vat = serializers.DecimalField(max_digits=15, decimal_places=2)
    ait = serializers.DecimalField(max_digits=15, decimal_places=2)
    at = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_duty = serializers.DecimalField(max_digits=15, decimal_places=2)
    landed_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
