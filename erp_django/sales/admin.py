"""
Sales Admin Configuration
"""
from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, Delivery


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer_name', 'status', 'total_amount', 'created_at']
    list_filter = ['status']
    search_fields = ['order_number', 'customer_name']
    inlines = [SalesOrderItemInline]


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ['order', 'item', 'quantity', 'delivery_date']
    list_filter = ['delivery_date']
