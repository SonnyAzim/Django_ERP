"""
Inventory API Views
"""
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from .models import Item, Transaction, StockAdjustment
from .serializers import (
    ItemSerializer, ItemCreateSerializer, ItemBulkUploadSerializer,
    StockUpdateSerializer, TransactionSerializer, StockAdjustmentSerializer
)


@api_view(['POST'])
@csrf_exempt
def bulk_upload_items(request):
    """CSRF-exempt bulk upload endpoint for inventory items."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        serializer = ItemBulkUploadSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Bulk upload validation errors: {serializer.errors}")
            return Response({
                'success': False,
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        items_data = serializer.validated_data['items']
        logger.info(f"Received {len(items_data)} items to upload")
        if items_data:
            logger.info(f"First item: {items_data[0]}")
        
        created = 0
        updated = 0
        errors = []
        
        for idx, item_data in enumerate(items_data):
            try:
                sku = item_data.get('sku')
                if not sku:
                    continue
                
                defaults = {
                    'name': item_data.get('name', ''),
                    'major_category': item_data.get('major_category', 'RAW MATERIAL'),
                    'minor_category': item_data.get('minor_category', ''),
                    'item_group': item_data.get('item_group', ''),
                    'fiscal_category': item_data.get('fiscal_category', ''),
                    'unit': item_data.get('unit', 'PCS'),
                    'current_stock': float(item_data.get('current_stock', 0)),
                    'price': float(item_data.get('price', 0)),
                    'source': item_data.get('source', 'local'),
                    'item_type': item_data.get('type', 'component'),
                    'lead_time_days': item_data.get('lead_time_days'),
                }
                
                item, is_new = Item.objects.update_or_create(
                    sku=sku,
                    defaults=defaults
                )
                
                if is_new:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({'index': idx, 'sku': sku, 'error': str(e)})
        
        return Response({
            'success': True,
            'created': created,
            'updated': updated,
            'errors': errors[:10]  # Limit error count
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ItemPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    pagination_class = ItemPagination
    filterset_fields = ['major_category', 'minor_category', 'source', 'item_type']
    search_fields = ['name', 'sku']

    def get_serializer_class(self):
        if self.action == 'create':
            return ItemCreateSerializer
        return ItemSerializer

    def get_queryset(self):
        queryset = Item.objects.all()
        
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(sku__icontains=search)
            )
        
        # Filter by major_category
        major_category = self.request.query_params.get('major_category', None)
        if major_category:
            queryset = queryset.filter(major_category=major_category)
        
        return queryset

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        item = self.get_object()
        quantity = float(request.data.get('quantity', 0))
        reason = request.data.get('reason', '')
        
        adjustment = StockAdjustment.objects.create(
            item=item,
            quantity_before=item.current_stock,
            quantity_after=item.current_stock + quantity,
            reason=reason,
            user=request.user
        )
        
        item.current_stock += quantity
        item.save()
        
        Transaction.objects.create(
            item=item,
            type='adjustment',
            quantity=quantity,
            note=reason,
            user=request.user
        )
        
        return Response({
            'success': True,
            'adjustment': StockAdjustmentSerializer(adjustment).data
        })

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        serializer = ItemBulkUploadSerializer(data=request.data)
        if serializer.is_valid():
            items_data = serializer.validated_data['items']
            created = 0
            updated = 0
            
            for item_data in items_data:
                sku = item_data.get('sku')
                if not sku:
                    continue
                
                defaults = {
                    'name': item_data.get('name', ''),
                    'major_category': item_data.get('major_category', 'RAW MATERIAL'),
                    'minor_category': item_data.get('minor_category', ''),
                    'item_group': item_data.get('item_group', ''),
                    'fiscal_category': item_data.get('fiscal_category', ''),
                    'unit': item_data.get('unit', 'PCS'),
                    'current_stock': float(item_data.get('current_stock', 0)),
                    'price': float(item_data.get('price', 0)),
                    'source': item_data.get('source', 'local'),
                    'item_type': item_data.get('type', 'component'),
                }
                
                item, is_new = Item.objects.update_or_create(
                    sku=sku,
                    defaults=defaults
                )
                
                if is_new:
                    created += 1
                else:
                    updated += 1
                    
                if float(item_data.get('current_stock', 0)) > 0:
                    Transaction.objects.create(
                        item=item,
                        type='adjustment',
                        quantity=item_data['current_stock'],
                        note='Initial stock upload',
                        user=request.user
                    )
            
            return Response({
                'success': True,
                'created': created,
                'updated': updated
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def bulk_update_stock(self, request):
        serializer = StockUpdateSerializer(data=request.data)
        if serializer.is_valid():
            updates = serializer.validated_data['updates']
            updated_count = 0
            
            for update in updates:
                sku = update.get('sku')
                quantity = float(update.get('quantity', 0))
                note = update.get('note', 'Bulk stock update via API')
                
                try:
                    item = Item.objects.get(sku=sku)
                    item.current_stock += quantity
                    if item.current_stock < 0:
                        item.current_stock = 0
                    item.save()
                    
                    Transaction.objects.create(
                        item=item,
                        type='receive' if quantity > 0 else 'adjustment',
                        quantity=abs(quantity),
                        note=note,
                        user=request.user
                    )
                    updated_count += 1
                except Item.DoesNotExist:
                    continue
            
            return Response({
                'success': True,
                'updated': updated_count
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def simple_list(self, request):
        items = Item.objects.values('id', 'name', 'sku', 'major_category')
        return Response(list(items))

    @action(detail=True, methods=['delete'])
    def soft_delete(self, request, pk=None):
        item = self.get_object()
        
        item.bom_as_parent.all().delete()
        item.bom_as_child.all().delete()
        item.transactions.all().delete()
        item.item_suppliers.all().delete()
        item.delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    filterset_fields = ['item', 'type']

    @action(detail=False, methods=['post'])
    def receive(self, request):
        item_id = request.data.get('item_id')
        quantity = float(request.data.get('quantity', 0))
        note = request.data.get('note', '')
        
        try:
            item = Item.objects.get(id=item_id)
            item.current_stock += quantity
            item.save()
            
            transaction = Transaction.objects.create(
                item=item,
                type='receive',
                quantity=quantity,
                note=note,
                user=request.user
            )
            
            return Response({
                'success': True,
                'transaction': TransactionSerializer(transaction).data
            })
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def sale(self, request):
        item_id = request.data.get('item_id')
        quantity = float(request.data.get('quantity', 0))
        note = request.data.get('note', '')
        
        try:
            item = Item.objects.get(id=item_id)
            
            if item.current_stock < quantity:
                return Response(
                    {'error': 'Insufficient stock'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item.current_stock -= quantity
            item.save()
            
            transaction = Transaction.objects.create(
                item=item,
                type='sale',
                quantity=quantity,
                note=note,
                user=request.user
            )
            
            return Response({
                'success': True,
                'transaction': TransactionSerializer(transaction).data
            })
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class StockAdjustmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockAdjustment.objects.all()
    serializer_class = StockAdjustmentSerializer
