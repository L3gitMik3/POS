from django.db import models

from core.models import BaseModel


class TillSession(models.Model):
    terminal_id = models.CharField(max_length=100)
    opened_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="opened_tills")
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closed_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="closed_tills")
    closed_at = models.DateTimeField(null=True, blank=True)
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Sale(BaseModel):
    receipt_number = models.CharField(max_length=50, unique=True)
    till_session = models.ForeignKey(TillSession, on_delete=models.PROTECT, related_name="sales")
    cashier = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="cashier_sales")
    customer = models.ForeignKey("sales.Customer", null=True, blank=True, on_delete=models.SET_NULL, related_name="sales")
    status = models.CharField(max_length=16, choices=[("completed", "Completed"), ("voided", "Voided"), ("returned", "Returned")], default="completed")
    payment_status = models.CharField(max_length=16, choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed")], default="pending")
    payment_method = models.CharField(max_length=16, choices=[("cash", "Cash"), ("mpesa", "M-Pesa")], default="cash")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    version = models.IntegerField(default=0)
    client_uuid = models.UUIDField(null=True, blank=True, unique=True)


class SaleLine(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="sale_lines")
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Customer(models.Model):
    phone_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    loyalty_points = models.IntegerField(default=0)


class LoyaltyRule(models.Model):
    points_per_currency_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    redemption_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)


class Return(models.Model):
    original_sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="returns")
    reason = models.CharField(max_length=255, blank=True)
    restock = models.BooleanField(default=True)


class ReturnLine(models.Model):
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)
