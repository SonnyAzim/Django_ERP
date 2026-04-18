"""
Forecast Admin Configuration
"""
from django.contrib import admin
from .models import Forecast, MRPResult


@admin.register(Forecast)
class ForecastAdmin(admin.ModelAdmin):
    list_display = ['item', 'month', 'quantity']
    list_filter = ['month']
    search_fields = ['item__sku', 'item__name']


@admin.register(MRPResult)
class MRPResultAdmin(admin.ModelAdmin):
    list_display = ['item', 'month', 'gross_requirement', 'projected_stock', 'planned_order']
    list_filter = ['month']
