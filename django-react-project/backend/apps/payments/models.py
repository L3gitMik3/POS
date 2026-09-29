from django.db import models

from core.models import TenantScopedModel


class MpesaTransaction(TenantScopedModel):
    sale = models.ForeignKey("sales.Sale", on_delete=models.PROTECT, related_name="mpesa_transactions")
    phone_number = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    checkout_request_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=255, blank=True)
    receipt_number = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=16, choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed"), ("cancelled", "Cancelled")], default="pending")
    result_code = models.CharField(max_length=50, blank=True)
    result_description = models.TextField(blank=True)
    raw_callback = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.checkout_request_id or self.receipt_number or str(self.id)
