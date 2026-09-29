from django.db import models

from core.models import TenantBaseModel, TenantScopedModel


class TillSession(TenantScopedModel):
    terminal_id = models.CharField(max_length=100)
    opened_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="opened_tills")
    opened_at = models.DateTimeField(auto_now_add=True)
    opening_float = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    closed_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="closed_tills")
    closed_at = models.DateTimeField(null=True, blank=True)
    counted_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Sale(TenantBaseModel):
    receipt_number = models.CharField(max_length=50)
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
    client_uuid = models.UUIDField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant_schema", "receipt_number"], name="uniq_receipt_per_tenant"),
            models.UniqueConstraint(fields=["tenant_schema", "client_uuid"], name="uniq_sale_client_uuid_per_tenant", condition=models.Q(client_uuid__isnull=False)),
        ]


class SaleLine(TenantScopedModel):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT, related_name="sale_lines")
    quantity = models.IntegerField(default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)


class Customer(TenantScopedModel):
    phone_number = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    loyalty_points = models.IntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant_schema", "phone_number"], name="uniq_customer_phone_per_tenant"),
        ]


class LoyaltyRule(TenantScopedModel):
    points_per_currency_unit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    redemption_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)


class Return(TenantScopedModel):
    original_sale = models.ForeignKey(Sale, on_delete=models.PROTECT, related_name="returns")
    reason = models.CharField(max_length=255, blank=True)
    restock = models.BooleanField(default=True)


class ReturnLine(TenantScopedModel):
    return_obj = models.ForeignKey(Return, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity = models.IntegerField(default=0)
