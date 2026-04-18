"""
Inventory Models - Items, Stock, and Transactions
"""
from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    MAJOR_CATEGORY_CHOICES = [
        ('RAW MATERIAL', 'Raw Material'),
        ('PACKAGING MATERIAL', 'Packaging Material'),
        ('SEMI-FINISHED GOODS', 'Semi-Finished Goods'),
        ('FINISHED GOODS', 'Finished Goods'),
    ]
    
    SOURCE_CHOICES = [
        ('local', 'Local'),
        ('foreign', 'Foreign'),
    ]
    
    TYPE_CHOICES = [
        ('component', 'Component'),
        ('product', 'Product'),
        ('assembly', 'Assembly'),
    ]

    name = models.CharField(max_length=255, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True, default='PCS')
    current_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    min_stock = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0, help_text='Landed cost in BDT')
    
    major_category = models.CharField(max_length=50, choices=MAJOR_CATEGORY_CHOICES, blank=True, null=True, db_index=True)
    minor_category = models.CharField(max_length=50, blank=True, null=True)
    item_group = models.CharField(max_length=100, blank=True, null=True)
    fiscal_category = models.CharField(max_length=50, blank=True, null=True)
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='local')
    item_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='component')
    lead_time_days = models.IntegerField(null=True, blank=True, help_text='Default lead time in days')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='items')

    class Meta:
        verbose_name_plural = 'Items'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sku} - {self.name}" if self.name else self.sku or 'Unnamed Item'

    @property
    def asset_value(self):
        stock = max(0, float(self.current_stock or 0))
        price = float(self.price or 0)
        return stock * price

    def get_lead_time(self):
        preferred = self.item_suppliers.filter(is_preferred=True).first()
        return preferred.lead_time_days if preferred else None

    def get_avg_consumption(self, days=30):
        from django.utils import timezone
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(days=days)
        total = self.transactions.filter(
            type__in=['sale', 'delivery', 'production'],
            timestamp__gte=cutoff
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        return float(total) / days


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('receive', 'Receive'),
        ('sale', 'Sale'),
        ('delivery', 'Delivery'),
        ('adjustment', 'Adjustment'),
        ('production', 'Production'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='transactions')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    note = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='transactions')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.type} - {self.item.sku}: {self.quantity}"


class StockAdjustment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='adjustments')
    quantity_before = models.DecimalField(max_digits=15, decimal_places=2)
    quantity_after = models.DecimalField(max_digits=15, decimal_places=2)
    reason = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.sku}: {self.quantity_before} -> {self.quantity_after}"
