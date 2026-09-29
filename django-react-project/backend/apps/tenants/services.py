from __future__ import annotations

from django.db import connection
from django.db import transaction
from django_tenants.utils import schema_context

from apps.accounts.models import User
from apps.tenants.models import Tenant


def seed_tenant_defaults(tenant):
    with schema_context(tenant.schema_name):
        default_owner, _ = User.objects.get_or_create(
            username=f"owner-{tenant.schema_name}",
            defaults={
                "full_name": "Tenant Owner",
                "role": "owner",
                "is_active": True,
                "tenant_schema": tenant.schema_name,
            },
        )
        if not default_owner.has_usable_password():
            default_owner.set_password("tenant-owner")
            default_owner.save()
    return default_owner


def provision_tenant(slug, name, owner_username, owner_password):
    tenant = Tenant.objects.create(
        schema_name=slug,
        name=name,
        slug=slug,
        status="provisioning",
    )

    try:
        with schema_context(tenant.schema_name):
            tenant.status = "active"
            tenant.save()
            owner = User.objects.create(
                username=owner_username,
                full_name=name,
                role="owner",
                is_active=True,
                tenant_schema=tenant.schema_name,
            )
            owner.set_password(owner_password)
            owner.save()
        return tenant
    except Exception:
        tenant.delete(force_drop=True)
        raise


def suspend_tenant(tenant):
    tenant.status = "suspended"
    tenant.save()


def activate_tenant(tenant):
    tenant.status = "active"
    tenant.save()
