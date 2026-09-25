from __future__ import annotations

from django.core.management.base import BaseCommand

from core.models import IdempotencyKey
from core.tenant_command import TenantCommand


class Command(TenantCommand, BaseCommand):
    help = "Prune expired idempotency keys in each tenant schema"
    job_name = "prune_idempotency_keys"

    def handle(self, *args, **options):
        self.run_for_all_tenants()

    def handle_tenant(self, tenant):
        # Placeholder: implement actual TTL pruning here when the tenant model is finalized.
        self.stdout.write(self.style.SUCCESS(f"Prune check for {tenant.schema_name}"))
