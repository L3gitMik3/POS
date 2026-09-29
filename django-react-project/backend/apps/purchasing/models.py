from django.db import models

from core.models import TenantScopedModel


class Supplier(TenantScopedModel):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class PurchaseOrder(TenantScopedModel):
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=32, choices=[
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("partially_received", "Partially Received"),
        ("fully_received", "Fully Received"),
        ("cancelled", "Cancelled"),
    ], default="draft")
    expected_date = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="purchase_orders")


class PurchaseOrderLine(TenantScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_ordered = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity_received_so_far = models.IntegerField(default=0)


class GoodsReceivedNote(TenantScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="grns")
    received_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="received_grns")
    delivery_note_ref = models.CharField(max_length=255, blank=True)


class GRNLine(TenantScopedModel):
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("inventory.Product", on_delete=models.PROTECT)
    quantity_received = models.IntegerField(default=0)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
