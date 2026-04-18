"""
Bill of Materials Models
"""
from django.db import models
from django.contrib.auth.models import User


class BoM(models.Model):
    parent = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='bom_as_parent',
        help_text='The finished/semi-finished good'
    )
    child = models.ForeignKey(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='bom_as_child',
        help_text='The raw material/component'
    )
    quantity = models.DecimalField(max_digits=15, decimal_places=4, help_text='Quantity of child needed per parent')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='bom_entries')

    class Meta:
        unique_together = ['parent', 'child']
        ordering = ['parent', 'child']
        verbose_name = 'Bill of Materials Entry'
        verbose_name_plural = 'Bill of Materials'

    def __str__(self):
        return f"{self.parent.sku} -> {self.child.sku}: {self.quantity}"

    def get_component_cost(self):
        qty = float(self.quantity)
        price = float(self.child.price or 0)
        return qty * price
