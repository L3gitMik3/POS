from django.core.management.base import BaseCommand

from core.tenant_command import TenantCommand


class Command(TenantCommand, BaseCommand):
    help = "Check low stock per tenant"
    job_name = "check_low_stock"

    def handle(self, *args, **options):
        self.run_for_all_tenants()

    def handle_tenant(self, tenant):
        self.stdout.write(self.style.SUCCESS(f"Low-stock check for {tenant.schema_name}"))
