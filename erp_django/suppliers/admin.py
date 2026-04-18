"""
Supplier Admin Configuration
"""
from django.contrib import admin
from .models import Supplier, ItemSupplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_name', 'email', 'phone', 'rating']
    list_filter = ['category', 'rating']
    search_fields = ['name', 'contact_name']


@admin.register(ItemSupplier)
class ItemSupplierAdmin(admin.ModelAdmin):
    list_display = ['item', 'supplier', 'lead_time_days', 'is_preferred']
    list_filter = ['is_preferred']
    search_fields = ['item__sku', 'supplier__name']
