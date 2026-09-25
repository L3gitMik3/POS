from django.db import models


class AuditLogEntry(models.Model):
    actor = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_entries")
    action = models.CharField(max_length=255)
    model_name = models.CharField(max_length=255)
    object_id = models.CharField(max_length=255)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["created_at"]),
        ]
