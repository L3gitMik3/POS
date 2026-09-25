from django.core.management.base import BaseCommand

from core.tenant_command import TenantCommand


class Command(TenantCommand, BaseCommand):
    help = "Scan dead stock per tenant"
    job_name = "dead_stock_scan"

    def handle(self, *args, **options):
        self.run_for_all_tenants()

    def handle_tenant(self, tenant):
        self.stdout.write(self.style.SUCCESS(f"Dead-stock scan for {tenant.schema_name}"))
