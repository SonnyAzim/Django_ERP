"""
Forecast API Views with MRP Engine
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .models import Forecast, MRPResult
from .serializers import ForecastSerializer
from inventory.models import Item
from bom.models import BoM


class ForecastListView(APIView):
    def get(self, request):
        item_id = request.query_params.get('item_id')
        month = request.query_params.get('month')
        
        queryset = Forecast.objects.all().select_related('item')
        
        # Filter for Finished Goods only
        item_category = request.query_params.get('category')
        if item_category == 'FG':
            queryset = queryset.filter(item__major_category='FINISHED GOODS')
        
        if item_id:
            queryset = queryset.filter(item_id=item_id)
        if month:
            queryset = queryset.filter(month=month)
        
        queryset = queryset.order_by('item__sku', 'month')
        serializer = ForecastSerializer(queryset, many=True)
        return Response(serializer.data)


class ForecastUploadView(APIView):
    def post(self, request):
        forecasts_data = request.data.get('forecasts', [])
        created = 0
        updated = 0
        
        for fc_data in forecasts_data:
            item_id = fc_data.get('item_id')
            month = fc_data.get('month')
            quantity = fc_data.get('quantity', 0)
            
            if not item_id or not month:
                continue
            
            try:
                forecast, is_new = Forecast.objects.update_or_create(
                    item_id=item_id,
                    month=month,
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


class RollingMonthsView(APIView):
    def get(self, request):
        today = datetime.now()
        months = []
        for i in range(12):
            month_date = today + relativedelta(months=i)
            months.append(month_date.strftime('%Y-%m'))
        return Response(months)


def calculate_safety_stock(item, target_month):
    target = datetime.strptime(target_month, '%Y-%m')
    total_demand = 0
    
    for i in range(2):
        month = target + relativedelta(months=i)
        month_str = month.strftime('%Y-%m')
        forecast = Forecast.objects.filter(item=item, month=month_str).first()
        if forecast:
            total_demand += float(forecast.quantity)
    
    avg_monthly = total_demand / 2 if total_demand > 0 else 0
    avg_consumption = item.get_avg_consumption(30)
    if avg_consumption > avg_monthly:
        avg_monthly = avg_consumption
    
    return avg_monthly * 0.5


def get_material_requirements(item, qty, visited=None):
    if visited is None:
        visited = {}
    
    bom_entries = BoM.objects.filter(parent=item).select_related('child')
    
    if not bom_entries.exists():
        if item.major_category in ['RAW MATERIAL', 'PACKAGING MATERIAL']:
            visited[item.id] = {
                'item_id': item.id,
                'sku': item.sku,
                'name': item.name,
                'quantity': qty,
                'current_stock': float(item.current_stock or 0),
                'shortage': max(0, qty - float(item.current_stock or 0)),
                'unit': item.unit
            }
        return visited
    
    for entry in bom_entries:
        get_material_requirements(entry.child, float(entry.quantity) * qty, visited)
    
    return visited


class MRPCalculateView(APIView):
    def post(self, request):
        today = datetime.now()
        months = []
        for i in range(12):
            month_date = today + relativedelta(months=i)
            months.append(month_date.strftime('%Y-%m'))
        
        results = []
        finished_goods = Item.objects.filter(major_category='FINISHED GOODS')
        
        for fg in finished_goods:
            current_stock = float(fg.current_stock or 0)
            mrp_entry = {
                'item_id': fg.id,
                'item_sku': fg.sku,
                'item_name': fg.name,
                'current_stock': current_stock,
                'months': []
            }
            
            for month in months:
                forecast = Forecast.objects.filter(item=fg, month=month).first()
                demand = float(forecast.quantity) if forecast else 0
                
                safety_stock = calculate_safety_stock(fg, month)
                projected = current_stock - demand
                
                planned_order = 0
                if projected < safety_stock:
                    planned_order = safety_stock - projected
                
                mrp_entry['months'].append({
                    'month': month,
                    'demand': demand,
                    'projected_stock': round(projected, 2),
                    'safety_stock': round(safety_stock, 2),
                    'planned_order': round(planned_order, 2)
                })
                
                current_stock = projected + planned_order
            
            results.append(mrp_entry)
        
        MRPResult.objects.all().delete()
        
        return Response({
            'success': True,
            'results': results
        })


class MaterialRequirementsView(APIView):
    def get(self, request):
        item_id = request.query_params.get('item_id')
        quantity = float(request.query_params.get('quantity', 1))
        
        if not item_id:
            return Response({'error': 'item_id required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
        
        requirements = get_material_requirements(item, quantity)
        
        return Response(list(requirements.values()))


class OrderPlanView(APIView):
    def get(self, request):
        today = datetime.now()
        months = []
        for i in range(12):
            month_date = today + relativedelta(months=i)
            months.append(month_date.strftime('%Y-%m'))
        
        order_plan = []
        
        raw_materials = Item.objects.filter(
            major_category__in=['RAW MATERIAL', 'PACKAGING MATERIAL']
        )
        
        for rm in raw_materials:
            total_requirement = 0
            preferred_link = rm.item_suppliers.filter(is_preferred=True).first()
            lead_time = preferred_link.lead_time_days if preferred_link else 30
            
            for month in months:
                forecast = Forecast.objects.filter(item=rm, month=month).first()
                if forecast:
                    total_requirement += float(forecast.quantity)
            
            avg_monthly = total_requirement / 12 if total_requirement > 0 else 0
            safety_stock = avg_monthly * 2
            
            current_stock = float(rm.current_stock or 0)
            
            if current_stock < safety_stock:
                order_qty = safety_stock - current_stock + (avg_monthly * 0.5)
                
                order_month_idx = 12 - lead_time // 30
                order_month = months[min(order_month_idx, 11)] if months else months[0]
                
                order_plan.append({
                    'sku': rm.sku,
                    'name': rm.name,
                    'current_stock': current_stock,
                    'safety_stock': round(safety_stock, 2),
                    'suggested_order': round(order_qty, 2),
                    'order_month': order_month,
                    'lead_time_days': lead_time,
                    'unit_price': float(preferred_link.unit_price or rm.price) if preferred_link else float(rm.price)
                })
        
        return Response(order_plan)
