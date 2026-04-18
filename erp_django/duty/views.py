"""
Duty API Views - HS Codes and Duty Calculator
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from decimal import Decimal

from .models import HSCode, ItemHSCode
from .serializers import (
    HSCodeSerializer, ItemHSCodeSerializer, 
    DutyCalculationSerializer, DutyCalculationResultSerializer
)


class HSCodeViewSet(viewsets.ModelViewSet):
    queryset = HSCode.objects.all()
    serializer_class = HSCodeSerializer
    search_fields = ['code', 'description']
    filterset_fields = ['code']

    @action(detail=True, methods=['post'])
    def calculate(self, request, pk=None):
        """Calculate duty for a given customs value"""
        hs_code = self.get_object()
        customs_value = float(request.data.get('customs_value', 0))
        
        result = hs_code.calculate_duty(customs_value)
        result['hs_code'] = hs_code.code
        result['description'] = hs_code.description
        
        return Response(result)

    @action(detail=False, methods=['post'])
    def calculate_batch(self, request):
        """Calculate duties for multiple items"""
        calculations = request.data.get('calculations', [])
        results = []
        
        for calc in calculations:
            hs_code_id = calc.get('hs_code_id')
            hs_code_str = calc.get('hs_code')
            customs_value = float(calc.get('customs_value', 0))
            
            try:
                if hs_code_id:
                    hs = HSCode.objects.get(id=hs_code_id)
                else:
                    hs = HSCode.objects.get(code=hs_code_str)
                
                result = hs.calculate_duty(customs_value)
                result['hs_code'] = hs.code
                result['description'] = hs.description
                results.append(result)
            except HSCode.DoesNotExist:
                results.append({
                    'error': f'HS Code not found: {hs_code_str or hs_code_id}',
                    'customs_value': customs_value
                })
        
        return Response(results)


class ItemHSCodeViewSet(viewsets.ModelViewSet):
    queryset = ItemHSCode.objects.all()
    serializer_class = ItemHSCodeSerializer
    filterset_fields = ['item', 'hs_code']

    @action(detail=False, methods=['post'])
    def link(self, request):
        """Link an HS code to an item"""
        item_id = request.data.get('item_id')
        hs_code_id = request.data.get('hs_code_id')
        
        link, created = ItemHSCode.objects.update_or_create(
            item_id=item_id,
            defaults={'hs_code_id': hs_code_id}
        )
        
        return Response({
            'success': True,
            'created': created,
            'link': ItemHSCodeSerializer(link).data
        })

    @action(detail=False, methods=['get'])
    def get_for_item(self, request):
        """Get HS code for an item"""
        item_id = request.query_params.get('item_id')
        if item_id:
            try:
                link = ItemHSCode.objects.get(item_id=item_id)
                return Response(ItemHSCodeSerializer(link).data)
            except ItemHSCode.DoesNotExist:
                return Response({'hs_code': None})
        return Response({'hs_code': None})


class DutyCalculatorViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate duty without needing to save HS code first"""
        serializer = DutyCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        customs_value = float(data['customs_value'])
        
        hs_code_id = data.get('hs_code_id')
        hs_code_str = data.get('hs_code')
        
        try:
            if hs_code_id:
                hs = HSCode.objects.get(id=hs_code_id)
            else:
                hs = HSCode.objects.get(code=hs_code_str)
            
            result = hs.calculate_duty(customs_value)
            result['hs_code'] = hs.code
            result['description'] = hs.description
            
            return Response(result)
        except HSCode.DoesNotExist:
            return Response(
                {'error': f'HS Code not found: {hs_code_str or hs_code_id}'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'])
    def import_codes(self, request):
        """Bulk import HS codes"""
        codes = request.data.get('codes', [])
        created = 0
        updated = 0
        
        for code_data in codes:
            code = code_data.get('code')
            if not code:
                continue
            
            defaults = {
                'description': code_data.get('description', ''),
                'cd': float(code_data.get('cd', 0)),
                'rd': float(code_data.get('rd', 0)),
                'sd': float(code_data.get('sd', 0)),
                'vat': float(code_data.get('vat', 0)),
                'ait': float(code_data.get('ait', 0)),
                'at': float(code_data.get('at', 0)),
            }
            
            hs, is_new = HSCode.objects.update_or_create(
                code=code,
                defaults=defaults
            )
            
            if is_new:
                created += 1
            else:
                updated += 1
        
        return Response({
            'success': True,
            'created': created,
            'updated': updated
        })
