"""
Supplier API Views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Supplier, ItemSupplier
from .serializers import SupplierSerializer, ItemSupplierSerializer, SupplierLinkSerializer
from inventory.models import Item


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    search_fields = ['name', 'contact_name', 'email']
    filterset_fields = ['category', 'rating']

    @action(detail=False, methods=['get'])
    def get_for_item(self, request):
        item_id = request.query_params.get('item_id')
        if item_id:
            links = ItemSupplier.objects.filter(item_id=item_id).select_related('supplier')
            serializer = ItemSupplierSerializer(links, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['post'])
    def link_item(self, request):
        serializer = SupplierLinkSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            
            link, created = ItemSupplier.objects.update_or_create(
                item_id=data['item_id'],
                supplier_id=data['supplier_id'],
                defaults={
                    'lead_time_days': data.get('lead_time_days', 7),
                    'unit_price': data.get('unit_price'),
                    'is_preferred': data.get('is_preferred', False)
                }
            )
            
            return Response({
                'success': True,
                'created': created,
                'link': ItemSupplierSerializer(link).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'])
    def unlink_item(self, request, pk=None):
        item_id = request.query_params.get('item_id')
        link_id = pk
        
        if link_id:
            try:
                link = ItemSupplier.objects.get(id=link_id)
                link.delete()
                return Response({'success': True})
            except ItemSupplier.DoesNotExist:
                pass
        
        return Response(
            {'error': 'Link not found'},
            status=status.HTTP_404_NOT_FOUND
        )


class ItemSupplierViewSet(viewsets.ModelViewSet):
    queryset = ItemSupplier.objects.all()
    serializer_class = ItemSupplierSerializer
    filterset_fields = ['item', 'supplier', 'is_preferred']

    @action(detail=True, methods=['post'])
    def set_preferred(self, request, pk=None):
        link = self.get_object()
        link.is_preferred = True
        link.save()
        return Response(ItemSupplierSerializer(link).data)
