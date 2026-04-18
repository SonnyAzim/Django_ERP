"""
Inventory Admin Configuration
"""
from django.contrib import admin
from .models import Item, Transaction, StockAdjustment


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['sku', 'name', 'major_category', 'minor_category', 'current_stock', 'price', 'source']
    list_filter = ['major_category', 'minor_category', 'source', 'item_type']
    search_fields = ['sku', 'name', 'minor_category']
    readonly_fields = ['created_at', 'updated_at', 'asset_value']
    list_per_page = 50


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['item', 'type', 'quantity', 'timestamp', 'user']
    list_filter = ['type', 'timestamp']
    search_fields = ['item__sku', 'item__name']


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ['item', 'quantity_before', 'quantity_after', 'reason', 'created_at']
    search_fields = ['item__sku']
