"""
Supplier Models
"""
from django.db import models
from django.contrib.auth.models import User


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    contact_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    rating = models.IntegerField(blank=True, null=True, help_text='1 to 5 stars')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='suppliers')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_total_linked_value(self):
        total = 0
        for link in self.item_suppliers.all():
            stock = float(link.item.current_stock or 0)
            price = float(link.unit_price or 0)
            total += stock * price
        return total


class ItemSupplier(models.Model):
    item = models.ForeignKey('inventory.Item', on_delete=models.CASCADE, related_name='item_suppliers')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='item_suppliers')
    lead_time_days = models.IntegerField(default=7)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    is_preferred = models.BooleanField(default=False, db_index=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['item', 'supplier']
        verbose_name = 'Item Supplier'
        verbose_name_plural = 'Item Suppliers'

    def __str__(self):
        pref = '★' if self.is_preferred else ''
        return f"{self.supplier.name} - {self.item.sku} ({self.lead_time_days}d) {pref}"

    def save(self, *args, **kwargs):
        if self.is_preferred:
            ItemSupplier.objects.filter(item=self.item, is_preferred=True).exclude(pk=self.pk).update(is_preferred=False)
        super().save(*args, **kwargs)
