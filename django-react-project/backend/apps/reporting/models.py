from django.db import models


class DailyReportSnapshot(models.Model):
    date = models.DateField(unique=True)
    gross_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discounts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mpesa_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_count = models.IntegerField(default=0)
    voided_count = models.IntegerField(default=0)
    returned_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    top_products = models.JSONField(default=list)
    generated_at = models.DateTimeField(auto_now_add=True)
