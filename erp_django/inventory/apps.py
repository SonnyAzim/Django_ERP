"""
Inventory app - Items, Stock, and Transaction Management
"""
from django.apps import AppConfig


class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventory'
