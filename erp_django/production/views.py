"""
Production Views - Manufacturing Logic
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction as db_transaction
from datetime import datetime

from .models import ProductionOrder, ProductionConsumption
from inventory.models import Item, Transaction
from bom.models import BoM


class ProductionOrderViewSet(viewsets.ModelViewSet):
    queryset = ProductionOrder.objects.all()
    filterset_fields = ['status', 'item']
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        item_id = request.data.get('item')
        quantity = float(request.data.get('quantity', 0))
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if item.major_category not in ['FINISHED GOODS', 'SEMI-FINISHED GOODS']:
            return Response(
                {'error': 'Only finished or semi-finished goods can be manufactured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shortages = self._check_components(item, quantity)
        if shortages:
            return Response({
                'success': False,
                'message': 'Insufficient stock for one or more components',
                'shortages': shortages
            }, status=status.HTTP_400_BAD_REQUEST)
        
        order_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        order = ProductionOrder.objects.create(
            order_number=order_number,
            item=item,
            quantity=quantity,
            created_by=request.user
        )
        
        self._deduct_components(order, quantity)
        
        item.current_stock += quantity
        item.save()
        
        Transaction.objects.create(
            item=item,
            type='production',
            quantity=quantity,
            note=f"Production order: {order_number}",
            user=request.user
        )
        
        return Response({
            'success': True,
            'order': {
                'id': order.id,
                'order_number': order.order_number,
                'item': item.sku,
                'quantity': float(quantity)
            }
        }, status=status.HTTP_201_CREATED)

    def _check_components(self, item, quantity):
        shortages = []
        
        bom_entries = BoM.objects.filter(parent=item).select_related('child')
        
        for entry in bom_entries:
            required_qty = float(entry.quantity) * quantity
            current_stock = float(entry.child.current_stock or 0)
            
            if current_stock < required_qty:
                shortages.append({
                    'item_id': entry.child.id,
                    'sku': entry.child.sku,
                    'name': entry.child.name,
                    'required': required_qty,
                    'current': current_stock,
                    'shortage': required_qty - current_stock
                })
                
                sub_shortages = self._check_components(entry.child, required_qty - current_stock)
                shortages.extend(sub_shortages)
        
        return shortages

    def _deduct_components(self, order, quantity):
        bom_entries = BoM.objects.filter(parent=order.item).select_related('child')
        
        for entry in bom_entries:
            qty_to_deduct = float(entry.quantity) * quantity
            
            entry.child.current_stock -= qty_to_deduct
            entry.child.save()
            
            ProductionConsumption.objects.create(
                order=order,
                item=entry.child,
                quantity_used=qty_to_deduct
            )
            
            Transaction.objects.create(
                item=entry.child,
                type='production',
                quantity=qty_to_deduct,
                note=f"Production consumption: {order.order_number}",
                user=order.created_by
            )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if order.status == 'completed':
            return Response(
                {'error': 'Completed orders cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        for consumption in order.consumptions.all():
            consumption.item.current_stock += consumption.quantity_used
            consumption.item.save()
            
            Transaction.objects.create(
                item=consumption.item,
                type='receive',
                quantity=consumption.quantity_used,
                note=f"Production cancelled: {order.order_number}",
                user=request.user
            )
        
        order.item.current_stock -= order.quantity
        order.item.save()
        
        order.status = 'cancelled'
        order.save()
        
        return Response({'success': True})

    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        orders_data = request.data.get('orders', [])
        created = 0
        errors = []
        
        for idx, order_data in enumerate(orders_data):
            try:
                item_id = order_data.get('item_id')
                quantity = float(order_data.get('quantity', 0))
                
                item = Item.objects.get(id=item_id)
                
                shortages = self._check_components(item, quantity)
                if shortages:
                    errors.append({'index': idx, 'error': 'shortage', 'shortages': shortages})
                    continue
                
                order_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
                order = ProductionOrder.objects.create(
                    order_number=order_number,
                    item=item,
                    quantity=quantity,
                    created_by=request.user
                )
                
                self._deduct_components(order, quantity)
                
                item.current_stock += quantity
                item.save()
                
                Transaction.objects.create(
                    item=item,
                    type='production',
                    quantity=quantity,
                    note=f"Production order: {order_number}",
                    user=request.user
                )
                
                created += 1
            except Exception as e:
                errors.append({'index': idx, 'error': str(e)})
        
        return Response({
            'created': created,
            'errors': errors
        })
