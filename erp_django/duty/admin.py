"""
Duty Admin Configuration
"""
from django.contrib import admin
from .models import HSCode, ItemHSCode


@admin.register(HSCode)
class HSCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'description', 'cd', 'rd', 'sd', 'vat']
    search_fields = ['code', 'description']


@admin.register(ItemHSCode)
class ItemHSCodeAdmin(admin.ModelAdmin):
    list_display = ['item', 'hs_code']
    search_fields = ['item__sku', 'hs_code__code']
