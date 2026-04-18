"""
Bill of Materials API Views with Explosion/Implosion
"""
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response

from .models import BoM
from .serializers import BoMSerializer, BoMEntrySerializer
from inventory.models import Item, Transaction


@api_view(['POST'])
@csrf_exempt
def bulk_upload_bom(request):
    """CSRF-exempt bulk upload endpoint for BoM entries."""
    entries_data = request.data.get('entries', [])
    created = 0
    updated = 0
    
    for entry_data in entries_data:
        parent_id = entry_data.get('parent_id')
        child_id = entry_data.get('child_id')
        quantity = entry_data.get('quantity', 1)
        
        if not parent_id or not child_id:
            continue
        
        try:
            entry, is_new = BoM.objects.update_or_create(
                parent_id=parent_id,
                child_id=child_id,
                defaults={'quantity': quantity}
            )
            if is_new:
                created += 1
            else:
                updated += 1
        except Exception:
            continue
    
    return Response({
        'success': True,
        'created': created,
        'updated': updated
    })


class BoMViewSet(viewsets.ModelViewSet):
    queryset = BoM.objects.all()
    serializer_class = BoMSerializer
    filterset_fields = ['parent', 'child']

    @action(detail=False, methods=['get'])
    def get_for_parent(self, request):
        parent_id = request.query_params.get('parent_id')
        if parent_id:
            entries = self.queryset.filter(parent_id=parent_id).select_related('child', 'parent')
            serializer = self.get_serializer(entries, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['get'])
    def get_for_child(self, request):
        child_id = request.query_params.get('child_id')
        if child_id:
            entries = self.queryset.filter(child_id=child_id).select_related('parent', 'child')
            serializer = self.get_serializer(entries, many=True)
            return Response(serializer.data)
        return Response([])

    @action(detail=False, methods=['get'])
    def explosion(self, request):
        """Get full BoM explosion for an item (all levels down)"""
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response({'error': 'item_id query parameter required', 'components': []}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found', 'components': []}, status=status.HTTP_404_NOT_FOUND)
        except ValueError:
            return Response({'error': 'Invalid item_id', 'components': []}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            result = self._explode(item, qty=1, level=0)
            return Response(result)
        except Exception as e:
            import traceback
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _explode(self, item, qty=1, level=0, visited=None):
        if visited is None:
            visited = set()
        
        # Validate item
        if not item or not hasattr(item, 'id'):
            return {'item': {}, 'components': [], 'total_cost': 0}
        
        if item.id in visited:
            return {'error': 'Circular reference detected', 'components': []}
        visited.add(item.id)
        
        components = []
        total_cost = 0
        
        try:
            bom_entries = BoM.objects.filter(parent_id=item.id).select_related('child')
        except Exception as e:
            return {'error': 'DB Error: ' + str(e), 'components': []}
        
        for entry in bom_entries:
            try:
                # Safe access
                child = entry.child
                if child is None:
                    continue
                
                # Get basic fields with safe access
                try:
                    child_id = child.pk
                    child_sku = getattr(child, 'sku', None) or ''
                    child_name = getattr(child, 'name', None) or ''
                    child_price = float(getattr(child, 'price', None) or 0)
                    child_stock = float(getattr(child, 'current_stock', None) or 0)
                    child_unit = getattr(child, 'unit', None) or 'PCS'
                except:
                    continue
                    
                child_qty = float(entry.quantity or 0) * qty
                child_cost = child_price * child_qty
                total_cost += child_cost
                
                # Check if child is SFG and recurse
                child_category = getattr(child, 'major_category', None)
                sub_components = []
                if child_category and 'SEMI' in child_category.upper():
                    sub_result = self._explode(child, qty=child_qty, level=level+1, visited=visited.copy())
                    if 'error' not in sub_result:
                        sub_components = sub_result.get('components', [])
                        total_cost += sub_result.get('total_cost', 0)
                
                component = {
                    'id': child_id,
                    'sku': str(child_sku),
                    'name': str(child_name),
                    'level': level,
                    'category': child_category,
                    'quantity': child_qty,
                    'unit_price': child_price,
                    'cost': child_cost,
                    'current_stock': child_stock,
                    'unit': str(child_unit),
                    'sub_components': sub_components
                }
                
                components.append(component)
            except Exception as e:
                continue
        
        # Safe access to item fields
        try:
            item_sku = getattr(item, 'sku', None) or ''
            item_name = getattr(item, 'name', None) or ''
        except:
            item_sku = ''
            item_name = ''
        
        return {
            'item': {
                'id': item.id,
                'sku': str(item_sku),
                'name': str(item_name),
                'quantity': qty,
                'level': level
            },
            'components': components,
            'total_cost': round(total_cost, 2)
        }

    @action(detail=False, methods=['get'])
    def where_used(self, request):
        """Find all items that use a specific component (implosion)"""
        child_id = request.query_params.get('child_id')
        if not child_id:
            return Response({'error': 'child_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(id=child_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        results = []
        bom_entries = BoM.objects.filter(child_id=child_id).select_related('parent')
        
        for entry in bom_entries:
            parent = entry.parent
            results.append({
                'parent_id': parent.id,
                'parent_sku': parent.sku,
                'parent_name': parent.name,
                'quantity_needed': float(entry.quantity),
                'current_stock': float(parent.current_stock or 0),
            })
        
        return Response(results)

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Upload multiple BoM entries at once"""
        entries_data = request.data.get('entries', [])
        created = 0
        updated = 0
        
        for entry_data in entries_data:
            parent_id = entry_data.get('parent_id')
            child_id = entry_data.get('child_id')
            quantity = entry_data.get('quantity', 1)
            
            if not parent_id or not child_id:
                continue
            
            try:
                entry, is_new = BoM.objects.update_or_create(
                    parent_id=parent_id,
                    child_id=child_id,
                    defaults={'quantity': quantity}
                )
                if is_new:
                    created += 1
                else:
                    updated += 1
            except Exception:
                continue
        
        return Response({
            'success': True,
            'created': created,
            'updated': updated
        })
