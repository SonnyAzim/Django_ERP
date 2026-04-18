"""
Supplier Serializers
"""
from rest_framework import serializers
from .models import Supplier, ItemSupplier


class ItemSupplierSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = ItemSupplier
        fields = [
            'id', 'item', 'supplier', 'supplier_name', 
            'lead_time_days', 'unit_price', 'is_preferred', 'created_at'
        ]


class SupplierSerializer(serializers.ModelSerializer):
    linked_items_count = serializers.SerializerMethodField()
    total_linked_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_name', 'email', 'phone', 'address',
            'category', 'rating', 'linked_items_count', 'total_linked_value',
            'created_at', 'updated_at'
        ]
    
    def get_linked_items_count(self, obj):
        return obj.item_suppliers.count()
    
    def get_total_linked_value(self, obj):
        return round(obj.get_total_linked_value(), 2)


class SupplierLinkSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    supplier_id = serializers.IntegerField()
    lead_time_days = serializers.IntegerField(required=False, default=7)
    unit_price = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    is_preferred = serializers.BooleanField(required=False, default=False)
