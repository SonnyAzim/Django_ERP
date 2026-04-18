"""
Valuation API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce

from inventory.models import Item


class ValuationSummaryView(APIView):
    def get(self, request):
        items = Item.objects.all()
        
        total_value = 0
        local_value = 0
        foreign_value = 0
        
        for item in items:
            stock = max(0, float(item.current_stock or 0))
            price = float(item.price or 0)
            value = stock * price
            
            total_value += value
            
            if item.source == 'local':
                local_value += value
            else:
                foreign_value += value
        
        return Response({
            'total_value': round(total_value, 2),
            'local_value': round(local_value, 2),
            'foreign_value': round(foreign_value, 2),
            'total_items': items.count(),
        })


class ValuationByCategoryView(APIView):
    def get(self, request):
        categories = Item.objects.values('major_category').annotate(
            item_count=Count('id'),
            total_value=Sum(
                Coalesce('current_stock', 0) * Coalesce('price', 0)
            )
        ).order_by('-total_value')
        
        grand_total = sum(c['total_value'] or 0 for c in categories)
        
        result = []
        for cat in categories:
            value = cat['total_value'] or 0
            percentage = (value / grand_total * 100) if grand_total > 0 else 0
            
            result.append({
                'major_category': cat['major_category'] or 'UNASSIGNED',
                'total_value': round(value, 2),
                'percentage': round(percentage, 2),
                'item_count': cat['item_count']
            })
        
        return Response(result)


class ValuationByItemGroupView(APIView):
    def get(self, request):
        groups = Item.objects.values('item_group').annotate(
            item_count=Count('id'),
            total_value=Sum(
                Coalesce('current_stock', 0) * Coalesce('price', 0)
            )
        ).filter(item_group__isnull=False).order_by('-total_value')
        
        result = []
        for grp in groups:
            result.append({
                'item_group': grp['item_group'] or 'N/A',
                'total_value': round(grp['total_value'] or 0, 2),
                'item_count': grp['item_count']
            })
        
        return Response(result)


class TopAssetsView(APIView):
    def get(self, request):
        limit = int(request.query_params.get('limit', 10))
        
        items = Item.objects.annotate(
            asset_value=Coalesce('current_stock', 0) * Coalesce('price', 0)
        ).order_by('-asset_value')[:limit]
        
        result = []
        for item in items:
            value = float(item.current_stock or 0) * float(item.price or 0)
            result.append({
                'id': item.id,
                'sku': item.sku,
                'name': item.name,
                'stock': float(item.current_stock or 0),
                'price': float(item.price or 0),
                'asset_value': round(value, 2),
                'source': item.source,
                'major_category': item.major_category
            })
        
        return Response(result)


class ExposureAnalysisView(APIView):
    def get(self, request):
        threshold = float(request.query_params.get('threshold', 20))
        
        categories = Item.objects.values('major_category').annotate(
            item_count=Count('id'),
            total_value=Sum(
                Coalesce('current_stock', 0) * Coalesce('price', 0)
            )
        ).order_by('-total_value')
        
        grand_total = sum(c['total_value'] or 0 for c in categories)
        
        high_exposure = []
        safe = []
        
        for cat in categories:
            value = cat['total_value'] or 0
            percentage = (value / grand_total * 100) if grand_total > 0 else 0
            
            cat_data = {
                'major_category': cat['major_category'] or 'UNASSIGNED',
                'total_value': round(value, 2),
                'percentage': round(percentage, 2),
                'item_count': cat['item_count']
            }
            
            if percentage > threshold:
                cat_data['is_high_exposure'] = True
                high_exposure.append(cat_data)
            else:
                cat_data['is_high_exposure'] = False
                safe.append(cat_data)
        
        return Response({
            'high_exposure': high_exposure,
            'safe': safe,
            'threshold': threshold
        })


class ValuationKPIView(APIView):
    def get(self, request):
        items = Item.objects.all()
        total_items = items.count()
        
        total_value = 0
        local_value = 0
        foreign_value = 0
        below_min = 0
        
        for item in items:
            stock = max(0, float(item.current_stock or 0))
            price = float(item.price or 0)
            value = stock * price
            
            total_value += value
            
            if item.source == 'local':
                local_value += value
            else:
                foreign_value += value
            
            if item.min_stock and stock < float(item.min_stock):
                below_min += 1
        
        categories = items.values('major_category').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return Response({
            'total_value': round(total_value, 2),
            'local_value': round(local_value, 2),
            'foreign_value': round(foreign_value, 2),
            'total_items': total_items,
            'below_min_stock': below_min,
            'categories': list(categories),
            'foreign_percentage': round(foreign_value / total_value * 100, 2) if total_value > 0 else 0
        })
