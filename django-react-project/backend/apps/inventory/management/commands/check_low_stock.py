from django.core.management.base import BaseCommand

from apps.inventory.services import low_stock_products
from apps.notifications.services import notify_low_stock
from core.tenant_command import TenantCommand


class Command(TenantCommand, BaseCommand):
    help = "Check low stock per tenant"
    job_name = "check_low_stock"

    def handle(self, *args, **options):
        self.run_for_all_tenants()

    def handle_tenant(self, tenant):
        products = list(low_stock_products())
        for product in products:
            notify_low_stock(product, product.stock_on_hand or 0)
        self.stdout.write(self.style.SUCCESS(f"Created or refreshed {len(products)} low-stock alert(s) for {tenant.schema_name}."))
