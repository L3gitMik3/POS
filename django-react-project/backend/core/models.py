import uuid

from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import connection, models


class TenantScopedQuerySet(models.QuerySet):
    def update(self, **kwargs):
        if "tenant_schema" in kwargs:
            raise ValidationError("Tenant ownership cannot be changed with a queryset update.")
        scoped_relation_fields = set()
        for field in self.model._meta.concrete_fields:
            if not field.is_relation or not field.many_to_one:
                continue
            try:
                field.remote_field.model._meta.get_field("tenant_schema")
            except FieldDoesNotExist:
                continue
            scoped_relation_fields.update((field.name, field.attname))
        if scoped_relation_fields.intersection(kwargs):
            raise ValidationError("Tenant-scoped relations must be changed through model validation.")
        return super().update(**kwargs)

    def bulk_create(self, objs, **kwargs):
        objs = list(objs)
        for obj in objs:
            obj._validate_tenant_scope(self.db)
        return super().bulk_create(objs, **kwargs)

    def bulk_update(self, objs, fields, **kwargs):
        if "tenant_schema" in fields:
            raise ValidationError("Tenant ownership cannot be changed with a bulk update.")
        objs = list(objs)
        for obj in objs:
            obj._validate_tenant_scope(self.db)
        return super().bulk_update(objs, fields, **kwargs)


class TenantScopedManager(models.Manager.from_queryset(TenantScopedQuerySet)):
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

    def _validate_tenant_scope(self, using):
        schema_name = getattr(connection, "schema_name", "public") or "public"
        if schema_name == "public":
            raise ValidationError("Tenant-owned records require an active tenant workspace.")
        if self.tenant_schema in {"", "public"}:
            self.tenant_schema = schema_name
        elif self.tenant_schema != schema_name:
            raise ValidationError("Cannot save a record into another tenant workspace.")

        for field in self._meta.concrete_fields:
            if not field.is_relation or not field.many_to_one:
                continue
            related_model = field.remote_field.model
            try:
                related_model._meta.get_field("tenant_schema")
            except FieldDoesNotExist:
                continue
            related_id = getattr(self, field.attname)
            if related_id is None:
                continue
            related_schema = (
                related_model._base_manager.using(using)
                .filter(pk=related_id)
                .values_list("tenant_schema", flat=True)
                .first()
            )
            if related_schema != schema_name:
                raise ValidationError({field.name: "Related record is not in the active tenant workspace."})

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or self._state.db or "default"
        self._validate_tenant_scope(using)
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
    key = models.CharField(max_length=255, db_index=True)
    endpoint = models.CharField(max_length=255)
    response_snapshot = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["created_at"])]
        constraints = [
            models.UniqueConstraint(fields=["tenant_schema", "key"], name="uniq_idempotency_key_per_tenant"),
        ]
