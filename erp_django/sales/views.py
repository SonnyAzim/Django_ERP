"""
Sales API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from datetime import datetime

from .models import SalesOrder, SalesOrderItem, Delivery
from .serializers import (
    SalesOrderSerializer, SalesOrderCreateSerializer, 
    SalesOrderItemSerializer, DeliverySerializer
)
from inventory.models import Item, Transaction


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    filterset_fields = ['status', 'customer_name']

    def get_serializer_class(self):
        if self.action == 'create':
            return SalesOrderCreateSerializer
        return SalesOrderSerializer

    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        order_items = data.pop('items')
        
        order = SalesOrder.objects.create(
            order_number=data['order_number'],
            customer_name=data['customer_name'],
            customer_contact=data.get('customer_contact', ''),
            notes=data.get('notes', ''),
            created_by=request.user
        )
        
        total = 0
        for item_data in order_items:
            item = Item.objects.get(id=item_data['item_id'])
            
            if item.major_category != 'FINISHED GOODS':
                raise ValueError(f"Sorry, only Finished Goods can be sold. {item.sku} is a {item.major_category}.")
            
            available = float(item.current_stock or 0)
            requested = item_data['quantity']
            if available < requested:
                raise ValueError(f"Insufficient stock for {item.sku}. Available: {available}, Requested: {requested}")
            
            unit_price = item_data.get('unit_price', item.price)
            qty = item_data['quantity']
            
            item.current_stock -= qty
            item.save()
            
            Transaction.objects.create(
                item=item,
                type='sale',
                quantity=qty,
                note=f"Sales order: {order.order_number}",
                user=request.user
            )
            
            item_total = qty * unit_price
            total += item_total
            
            SalesOrderItem.objects.create(
                order=order,
                item=item,
                quantity=qty,
                unit_price=unit_price,
                total=item_total
            )
        
        order.total_amount = total
        order.save()
        
        return Response(
            SalesOrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        order = self.get_object()
        item_id = request.data.get('item_id')
        quantity = float(request.data.get('quantity', 0))
        notes = request.data.get('notes', '')
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        order_item = order.items.filter(item_id=item_id).first()
        if not order_item:
            return Response({'error': 'Item not in order'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivered_qty = order.deliveries.filter(item_id=item_id).aggregate(
            total=models.Sum('quantity')
        )['total'] or 0
        
        remaining = float(order_item.quantity) - delivered_qty
        if quantity > remaining:
            quantity = remaining
        
        Delivery.objects.create(
            order=order,
            item=item,
            quantity=quantity,
            notes=notes,
            delivered_by=request.user
        )
        
        item.current_stock -= quantity
        item.save()
        
        Transaction.objects.create(
            item=item,
            type='delivery',
            quantity=quantity,
            note=f"Delivery for order: {order.order_number}",
            user=request.user
        )
        
        return Response({'success': True, 'quantity_delivered': quantity})

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        order = self.get_object()
        if order.status != 'pending':
            return Response(
                {'error': 'Order cannot be confirmed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        order.status = 'confirmed'
        order.save()
        return Response(SalesOrderSerializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status == 'delivered':
            return Response(
                {'error': 'Delivered orders cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for order_item in order.items.all():
            order_item.item.current_stock += order_item.quantity
            order_item.item.save()
        
        order.status = 'cancelled'
        order.save()
        
        return Response(SalesOrderSerializer(order).data)

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        orders_data = request.data.get('orders', [])
        created = 0
        errors = []
        
        for idx, order_data in enumerate(orders_data):
            try:
                data = SalesOrderCreateSerializer(data=order_data)
                if data.is_valid():
                    order_items = data.validated_data.pop('items')
                    
                    order = SalesOrder.objects.create(
                        order_number=data.validated_data['order_number'],
                        customer_name=data.validated_data['customer_name'],
                        customer_contact=data.validated_data.get('customer_contact', ''),
                        notes=data.validated_data.get('notes', ''),
                        created_by=request.user
                    )
                    
                    total = 0
                    for item_data in order_items:
                        item = Item.objects.get(id=item_data['item_id'])
                        unit_price = item_data.get('unit_price', item.price)
                        qty = item_data['quantity']
                        item_total = qty * unit_price
                        total += item_total
                        
                        SalesOrderItem.objects.create(
                            order=order,
                            item=item,
                            quantity=qty,
                            unit_price=unit_price,
                            total=item_total
                        )
                    
                    order.total_amount = total
                    order.save()
                    created += 1
                else:
                    errors.append({'index': idx, 'errors': data.errors})
            except Exception as e:
                errors.append({'index': idx, 'error': str(e)})
        
        return Response({
            'created': created,
            'errors': errors
        })


class DeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    filterset_fields = ['order', 'item']
