from django.db import models

from core.models import TenantScopedModel


class Notification(TenantScopedModel):
    type = models.CharField(max_length=64, choices=[
        ("low_stock", "Low Stock"),
        ("dead_stock", "Dead Stock"),
        ("mpesa_failed", "M-Pesa Failed"),
        ("system_error", "System Error"),
    ])
    message = models.TextField()
    reference_id = models.CharField(max_length=255, blank=True)
    dedupe_key = models.CharField(max_length=255, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant_schema", "dedupe_key"], name="uniq_notification_dedupe_key", condition=models.Q(dedupe_key__isnull=False)),
        ]
