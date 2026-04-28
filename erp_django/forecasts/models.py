"""
Forecast and MRP Models
"""
from django.db import models
from django.contrib.auth.models import User

class Forecast(models.Model):
    item = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='forecasts'
    )
    month = models.CharField(max_length=7, help_text='YYYY-MM format')
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='forecasts')
    
    class Meta:
        unique_together = ['item', 'month']
        ordering = ['month']
        verbose_name = 'Forecast'
        verbose_name_plural = 'Forecasts'
    
    def __str__(self):
        return f"{self.item.sku} - {self.month}: {self.quantity}"


class MRPResult(models.Model):
    item = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='mrp_results'
    )
    month = models.CharField(max_length=7)
    gross_requirement = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    projected_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    planned_order = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    safety_stock = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['item', 'month']
        ordering = ['month']
        verbose_name = 'MRP Result'
        verbose_name_plural = 'MRP Results'
    
    def __str__(self):
        return f"MRP: {self.item.sku} - {self.month}"


class Pipeline(models.Model):
    """Track ordered items until they arrive"""
    STATUS_CHOICES = [
        ('ordered', 'Ordered'),
        ('shipped', 'Shipped'),
        ('in_transit', 'In Transit'),
        ('received', 'Received'),
    ]
    
    item = models.ForeignKey('inventory.Item', on_delete=models.CASCADE, related_name='pipeline')
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ordered')
    order_date = models.DateField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    
    supplier = models.ForeignKey(
        'suppliers.Supplier', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='pipeline'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order_date']
        verbose_name = 'Pipeline Item'
        verbose_name_plural = 'Pipeline Items'
    
    def __str__(self):
        return f"{self.sku} - {self.quantity} ({self.status})"
    
    def save(self, *args, **kwargs):
        # When marked as received, add to inventory stock
        if self.status == 'received' and not self.received_date:
            self.received_date = models.timezone.now().date()
            # Add to inventory
            self.item.current_stock = (self.item.current_stock or 0) + float(self.quantity)
            self.item.save()
        super().save(*args, **kwargs)
