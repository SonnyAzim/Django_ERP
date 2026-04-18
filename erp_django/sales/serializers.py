"""
Sales Serializers
"""
from rest_framework import serializers
from .models import SalesOrder, SalesOrderItem, Delivery


class SalesOrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source='item.name', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = ['id', 'item', 'item_name', 'item_sku', 'quantity', 'unit_price', 'total']


class SalesOrderSerializer(serializers.ModelSerializer):
    items = SalesOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer_name', 'customer_contact',
            'status', 'total_amount', 'notes', 'items', 'created_at'
        ]


class SalesOrderCreateSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    customer_name = serializers.CharField()
    customer_contact = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    items = serializers.ListField(
        child=serializers.DictField()
    )


class DeliverySerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    item_sku = serializers.CharField(source='item.sku', read_only=True)
    
    class Meta:
        model = Delivery
        fields = ['id', 'order', 'order_number', 'item', 'item_sku', 
                   'quantity', 'delivery_date', 'notes']
