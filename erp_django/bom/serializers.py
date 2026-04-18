"""
Bill of Materials Serializers
"""
from rest_framework import serializers
from .models import BoM
from inventory.models import Item


class BoMSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    parent_sku = serializers.CharField(source='parent.sku', read_only=True)
    child_name = serializers.CharField(source='child.name', read_only=True)
    child_sku = serializers.CharField(source='child.sku', read_only=True)
    component_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = BoM
        fields = [
            'id', 'parent', 'parent_name', 'parent_sku',
            'child', 'child_name', 'child_sku',
            'quantity', 'component_cost', 'created_at'
        ]
    
    def get_component_cost(self, obj):
        return round(obj.get_component_cost(), 2)


class BoMEntrySerializer(serializers.Serializer):
    child_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=15, decimal_places=4)


class ExplosionResultSerializer(serializers.Serializer):
    item = serializers.DictField()
    components = serializers.ListField(child=serializers.DictField())
    total_cost = serializers.DecimalField(max_digits=15, decimal_places=2)
