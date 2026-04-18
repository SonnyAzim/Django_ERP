"""
Sales Models
"""
from django.db import models
from django.contrib.auth.models import User


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True)
    customer_name = models.CharField(max_length=255)
    customer_contact = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sales_orders')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'

    def __str__(self):
        return f"{self.order_number} - {self.customer_name}"


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('inventory.Item', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total = models.DecimalField(max_digits=15, decimal_places=2)

    def __str__(self):
        return f"{self.order.order_number} - {self.item.sku}"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class Delivery(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='deliveries')
    item = models.ForeignKey('inventory.Item', on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=15, decimal_places=2)
    delivery_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    delivered_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='deliveries')

    def __str__(self):
        return f"Delivery: {self.order.order_number} - {self.item.sku}"
