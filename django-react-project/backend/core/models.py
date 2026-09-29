import uuid

from django.core.exceptions import ValidationError
from django.db import connection, models


class TenantScopedManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        schema_name = getattr(connection, "schema_name", "public")
        if schema_name == "public":
            return queryset.none()
        return queryset.filter(tenant_schema=schema_name)


class TenantScopedModel(models.Model):
    """Tenant-owned data with a logical schema key for single-file SQLite dev."""

    tenant_schema = models.CharField(max_length=63, blank=True, default="", db_index=True)

    objects = TenantScopedManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        schema_name = getattr(connection, "schema_name", "public") or "public"
        if schema_name == "public":
            raise ValidationError("Tenant-owned records require an active tenant workspace.")
        if self.tenant_schema in {"", "public"}:
            self.tenant_schema = schema_name
        elif self.tenant_schema != schema_name:
            raise ValidationError("Cannot save a record into another tenant workspace.")
        return super().save(*args, **kwargs)


class BaseModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantBaseModel(TenantScopedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IdempotencyKey(TenantScopedModel):
    key = models.CharField(max_length=255, unique=True, db_index=True)
    endpoint = models.CharField(max_length=255)
    response_snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["created_at"])]
