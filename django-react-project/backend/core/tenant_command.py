from __future__ import annotations

import logging
from abc import ABC, abstractmethod

from django.db import connection

logger = logging.getLogger("django")


class TenantCommand(ABC):
    job_name = "base-tenant-command"

    def run_for_all_tenants(self):
        from apps.tenants.models import Tenant

        failures = []
        for tenant in Tenant.objects.filter(status="active"):
            try:
                if connection.vendor == "postgresql":
                    with connection.schema_context(tenant.schema_name):
                        self.handle_tenant(tenant)
                else:
                    previous_schema = getattr(connection, "schema_name", "public")
                    try:
                        connection.set_schema(tenant.schema_name)
                        self.handle_tenant(tenant)
                    finally:
                        connection.set_schema(previous_schema)
            except Exception as exc:  # pragma: no cover - command runner safety
                logger.exception("TenantCommand failed for %s", tenant.schema_name)
                failures.append((tenant.schema_name, str(exc)))
        if failures:
            raise RuntimeError(f"Tenant command failed for: {failures}")

    @abstractmethod
    def handle_tenant(self, tenant):
        raise NotImplementedError
