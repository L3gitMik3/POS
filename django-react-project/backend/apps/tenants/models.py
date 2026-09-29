from django.db import models
from django.db import connection
from django_tenants.models import DomainMixin, TenantMixin


class Tenant(TenantMixin):
    name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=160, blank=True, default="")
    slug = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=32, choices=[
        ("provisioning", "Provisioning"),
        ("active", "Active"),
        ("suspended", "Suspended"),
    ], default="provisioning")
    created_on = models.DateField(auto_now_add=True)
    auto_drop_schema = False

    def save(self, *args, **kwargs):
        if connection.vendor == "sqlite":
            create_schema = self.auto_create_schema
            self.auto_create_schema = False
            try:
                return super().save(*args, **kwargs)
            finally:
                self.auto_create_schema = create_schema
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Domain(DomainMixin):
    pass


class MpesaCallbackRoute(models.Model):
    checkout_request_id = models.CharField(max_length=255, unique=True)
    tenant_schema = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.checkout_request_id} -> {self.tenant_schema}"
