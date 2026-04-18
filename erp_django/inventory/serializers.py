"""
Inventory Serializers
"""
from rest_framework import serializers
from .models import Item, Transaction, StockAdjustment


class TransactionSerializer(serializers.ModelSerializer):
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'item', 'item_sku', 'type', 'quantity', 'timestamp', 'note']
        read_only_fields = ['timestamp']


class ItemSerializer(serializers.ModelSerializer):
    asset_value = serializers.SerializerMethodField()
    lead_time = serializers.SerializerMethodField()
    avg_consumption = serializers.SerializerMethodField()
    preferred_supplier = serializers.SerializerMethodField()
    current_stock = serializers.FloatField()
    price = serializers.FloatField()
    min_stock = serializers.FloatField(required=False, allow_null=True)
    
    class Meta:
        model = Item
        fields = [
            'id', 'name', 'sku', 'description', 'unit', 'current_stock', 
            'min_stock', 'price', 'major_category', 'minor_category', 
            'item_group', 'fiscal_category', 'source', 'item_type',
            'lead_time_days', 'asset_value', 'lead_time', 'avg_consumption', 'preferred_supplier',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_asset_value(self, obj):
        return float(obj.current_stock or 0) * float(obj.price or 0)
    
    def get_lead_time(self, obj):
        return obj.get_lead_time()
    
    def get_avg_consumption(self, obj):
        return round(obj.get_avg_consumption(30), 2)
    
    def get_preferred_supplier(self, obj):
        pref = obj.item_suppliers.filter(is_preferred=True).first()
        if pref:
            return {
                'id': pref.supplier.id,
                'name': pref.supplier.name,
                'lead_time_days': pref.lead_time_days
            }
        return None


class ItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = [
            'name', 'sku', 'description', 'unit', 'current_stock',
            'min_stock', 'price', 'major_category', 'minor_category',
            'item_group', 'fiscal_category', 'source', 'item_type',
            'lead_time_days'
        ]


class ItemBulkUploadSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField())


class StockUpdateSerializer(serializers.Serializer):
    updates = serializers.ListField(
        child=serializers.DictField()
    )


class StockAdjustmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustment
        fields = ['id', 'item', 'quantity_before', 'quantity_after', 'reason', 'created_at']
