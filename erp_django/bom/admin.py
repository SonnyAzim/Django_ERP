"""
BoM Admin Configuration
"""
from django.contrib import admin
from .models import BoM


@admin.register(BoM)
class BoMAdmin(admin.ModelAdmin):
    list_display = ['parent', 'child', 'quantity', 'created_at']
    list_filter = ['parent__major_category']
    search_fields = ['parent__sku', 'child__sku']
