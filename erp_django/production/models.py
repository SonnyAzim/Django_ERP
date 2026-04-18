"""
Production Models - Manufacturing Orders
"""
from django.db import models
from django.contrib.auth.models import User


class ProductionOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    item = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='production_orders'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='production_orders')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.item.sku}: {self.quantity}"


class ProductionConsumption(models.Model):
    """Tracks raw material consumption during production"""
    order = models.ForeignKey(
        ProductionOrder, 
        on_delete=models.CASCADE, 
        related_name='consumptions'
    )
    item = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='production_consumptions'
    )
    quantity_used = models.DecimalField(max_digits=15, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.order.order_number} - {self.item.sku}: {self.quantity_used}"
