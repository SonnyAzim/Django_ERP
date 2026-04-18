"""
Duty and HS Code Models
"""
from django.db import models
from django.contrib.auth.models import User


class HSCode(models.Model):
    code = models.CharField(max_length=20, unique=True, db_index=True)
    description = models.TextField(blank=True, null=True)
    cd = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Customs Duty %')
    rd = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Regulatory Duty %')
    sd = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Supplementary Duty %')
    vat = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='VAT %')
    ait = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Advance Income Tax %')
    at = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Advance Tax %')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='hs_codes')

    class Meta:
        verbose_name = 'HS Code'
        verbose_name_plural = 'HS Codes'
        ordering = ['code']

    def __str__(self):
        return self.code

    def calculate_duty(self, customs_value):
        cv = float(customs_value)
        self.cd_amt = cv * float(self.cd) / 100
        self.rd_amt = cv * float(self.rd) / 100
        self.sd_amt = (cv + self.cd_amt) * float(self.sd) / 100
        self.vat_base = cv + self.cd_amt + self.rd_amt + self.sd_amt
        self.vat_amt = self.vat_base * float(self.vat) / 100
        self.ait_amt = self.vat_base * float(self.ait) / 100
        self.at_amt = (cv + self.cd_amt + self.rd_amt) * float(self.at) / 100
        self.total_duty = self.cd_amt + self.rd_amt + self.sd_amt + self.vat_amt + self.ait_amt + self.at_amt
        return {
            'customs_value': cv,
            'cd': round(self.cd_amt, 2),
            'rd': round(self.rd_amt, 2),
            'sd': round(self.sd_amt, 2),
            'vat': round(self.vat_amt, 2),
            'ait': round(self.ait_amt, 2),
            'at': round(self.at_amt, 2),
            'total_duty': round(self.total_duty, 2),
            'landed_cost': round(cv + self.total_duty, 2),
        }


class ItemHSCode(models.Model):
    item = models.OneToOneField(
        'inventory.Item', 
        on_delete=models.CASCADE, 
        related_name='hs_code_link'
    )
    hs_code = models.ForeignKey(HSCode, on_delete=models.SET_NULL, null=True, related_name='items')

    def __str__(self):
        return f"{self.item.sku} - {self.hs_code.code if self.hs_code else 'N/A'}"
