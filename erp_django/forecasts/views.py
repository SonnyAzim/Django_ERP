"""
Forecast API Views with MRP Engine
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from datetime import datetime
from dateutil.relativedelta import relativedelta

from .models import Forecast, MRPResult
from .serializers import ForecastSerializer
from inventory.models import Item
from bom.models import BoM


class ForecastPagination(PageNumberPagination):
    page_size = 1000
    page_size_query_param = 'page_size'
    max_page_size = 5000


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
        
        # Add pagination for large datasets
        paginator = ForecastPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = ForecastSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = ForecastSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        forecasts_data = []
        
        # Handle array format from bulk upload
        if isinstance(request.data, list):
            forecasts_data = request.data
        elif isinstance(request.data, dict) and 'forecasts' in request.data:
            forecasts_data = request.data['forecasts']
        
        created = 0
        updated = 0
        
        for fc_data in forecasts_data:
            item_id = fc_data.get('item')
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
        month_labels = []
        for i in range(12):
            month_date = today + relativedelta(months=i)
            months.append(month_date.strftime('%Y-%m'))
            month_labels.append(month_date.strftime('%b-%Y'))  # e.g., "May-2026"
        
        # Get all forecasts for FG items
        all_forecasts = Forecast.objects.filter(
            item__major_category='FINISHED GOODS'
        ).select_related('item')
        
        # Month mapping from forecast format to API format
        month_convert = {
            'Jan-2026': '2026-01', 'Feb-2026': '2026-02', 'Mar-2026': '2026-03',
            'Apr-2026': '2026-04', 'May-2026': '2026-05', 'Jun-2026': '2026-06',
            'Jul-2026': '2026-07', 'Aug-2026': '2026-08', 'Sep-2026': '2026-09',
            'Oct-2026': '2026-10', 'Nov-2026': '2026-11', 'Dec-2026': '2026-12',
            'Jan-2027': '2027-01', 'Feb-2027': '2027-02', 'Mar-2027': '2027-03'
        }
        
        # Convert forecasts to dict by item and month
        forecast_dict = {}
        for fc in all_forecasts:
            month_key = month_convert.get(fc.month, fc.month)
            key = (fc.item_id, month_key)
            forecast_dict[key] = float(fc.quantity)
        
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
            
            for i, month in enumerate(months):
                demand = forecast_dict.get((fg.id, month), 0)
                
                # Calculate average demand from last 2 months
                total_recent = 0
                for j in range(max(0, i-1), i+1):
                    total_recent += forecast_dict.get((fg.id, months[j]), 0)
                avg_monthly = total_recent / 2 if i > 0 else demand
                if avg_monthly == 0:
                    avg_monthly = demand
                
                # Get lead time for this item (in days, convert to months)
                lead_time = getattr(fg, 'lead_time_days', None) or 0
                lead_time_months = max(1, int(lead_time / 30) + 1) if lead_time else 1
                
                # Safety stock = avg demand × (lead_time_months + buffer)
                safety_stock = max(avg_monthly * lead_time_months, 10)
                
                projected = current_stock - demand
                
                planned_order = 0
                if projected < safety_stock:
                    planned_order = safety_stock - projected
                
                mrp_entry['months'].append({
                    'month': month_labels[i],
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
        
        # Get options from query params
        try:
            months_to_use = int(request.query_params.get('months', 12))
        except:
            months_to_use = 12
        
        consider_fg_stock = request.query_params.get('fg_stock', 'true').lower() == 'true'
        consider_sfg_stock = request.query_params.get('sfg_stock', 'true').lower() == 'true'
        consider_rm_stock = request.query_params.get('rm_stock', 'true').lower() == 'true'
        
        months = []
        for i in range(months_to_use):
            month_date = today + relativedelta(months=i)
            months.append(month_date.strftime('%Y-%m'))
        
        order_plan = []
        
        # Get all Raw Materials and Packaging Materials
        raw_materials = Item.objects.filter(
            major_category__in=['RAW MATERIAL', 'PACKAGING MATERIAL']
        )
        
        # Get all Finished Goods forecasts
        fg_forecasts = Forecast.objects.filter(
            item__major_category='FINISHED GOODS'
        ).select_related('item')
        
        # Aggregate FG demand by month
        fg_demand = {}
        for fc in fg_forecasts:
            if fc.month not in fg_demand:
                fg_demand[fc.month] = 0
            fg_demand[fc.month] += float(fc.quantity)
        
        total_fg_demand = sum(fg_demand.values())
        avg_fg_monthly = total_fg_demand / len(months) if months else 0
        
        for rm in raw_materials:
            # Check if this RM is used in any FG BoM
            bom_entries = BoM.objects.filter(child=rm).select_related('parent')
            
            # Get effective stock based on options
            effective_stock = float(rm.current_stock or 0) if consider_rm_stock else 0
            
            if not bom_entries.exists():
                # Not used in BoM - skip
                continue
            
            # Calculate RM requirement from FG BoM (considering SFG chain)
            rm_demand_total = 0
            for bom in bom_entries:
                parent = bom.parent
                
                # Check if parent is SFG
                if parent.major_category and 'SEMI' in parent.major_category.upper():
                    # SFG level - check if this SFG is used in any FG BoM
                    sfg_bom_entries = BoM.objects.filter(child=parent).select_related('parent')
                    
                    sfg_stock = float(parent.current_stock or 0) if consider_sfg_stock else 0
                    
                    for sfg_bom in sfg_bom_entries:
                        fg = sfg_bom.parent
                        fg_stock = float(fg.current_stock or 0) if consider_fg_stock else 0
                        
                        for month in months:
                            month_demand = fg_demand.get(month, 0)
                            if consider_fg_stock and fg_stock > 0:
                                month_demand = max(0, month_demand - fg_stock)
                            if consider_sfg_stock and sfg_stock > 0:
                                month_demand = max(0, month_demand - sfg_stock)
                            
                            rm_demand_total += float(bom.quantity) * float(sfg_bom.quantity) * month_demand
                
                else:
                    # Direct FG parent
                    fg = parent
                    fg_stock = float(fg.current_stock or 0) if consider_fg_stock else 0
                    
                    for month in months:
                        month_demand = fg_demand.get(month, 0)
                        if consider_fg_stock and fg_stock > 0:
                            month_demand = max(0, month_demand - fg_stock)
                        
                        rm_demand_total += float(bom.quantity) * month_demand
            
            avg_monthly = rm_demand_total / len(months) if months else 0
            safety_stock = max(avg_monthly * 2, 50)
            current_stock = effective_stock
            
            # Calculate order if below safety stock
            if current_stock < safety_stock:
                preferred_link = rm.item_suppliers.filter(is_preferred=True).first()
                lead_time = preferred_link.lead_time_days if preferred_link else 30
                order_qty = (safety_stock - current_stock) * 1.2
                
                order_month_idx = min(12 - (lead_time // 30), 11) if lead_time else 0
                order_month = months[order_month_idx] if months else '2026-05'
                
                order_plan.append({
                    'sku': rm.sku,
                    'name': rm.name,
                    'current_stock': current_stock,
                    'safety_stock': round(safety_stock, 2),
                    'suggested_order': round(order_qty, 2),
                    'order_month': order_month,
                    'lead_time_days': lead_time,
                    'unit_price': float(preferred_link.unit_price or rm.price) if preferred_link else float(rm.price or 0)
                })
        
        return Response(order_plan)
