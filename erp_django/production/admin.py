"""
Production Admin Configuration
"""
from django.contrib import admin
from .models import ProductionOrder, ProductionConsumption


class ConsumptionInline(admin.TabularInline):
    model = ProductionConsumption
    extra = 0


@admin.register(ProductionOrder)
class ProductionOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'item', 'quantity', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order_number', 'item__sku']
    inlines = [ConsumptionInline]
