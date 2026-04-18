"""
Valuation Models - Stock Valuation and Financials
"""
from django.db import models
from django.contrib.auth.models import User


class StockValuation(models.Model):
    item = models.OneToOneField(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='valuation'
    )
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    local_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    foreign_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Stock Valuation'
        verbose_name_plural = 'Stock Valuations'

    def __str__(self):
        return f"{self.item.sku}: {self.current_value}"


class ValuationSummary(models.Model):
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    local_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    foreign_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_items = models.IntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Valuation Summary'
        verbose_name_plural = 'Valuation Summaries'

    def __str__(self):
        return f"Total: {self.total_value}"


class CategoryValue(models.Model):
    major_category = models.CharField(max_length=50)
    total_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    item_count = models.IntegerField(default=0)
    
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category Value'
        verbose_name_plural = 'Category Values'
        ordering = ['-total_value']

    def __str__(self):
        return f"{self.major_category}: {self.total_value}"
