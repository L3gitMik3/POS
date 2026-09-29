from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.inventory.services import dead_stock_products
from apps.notifications.services import notify
from core.tenant_command import TenantCommand


class Command(TenantCommand, BaseCommand):
    help = "Scan dead stock per tenant"
    job_name = "dead_stock_scan"

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=90, help="Days without stock movement before an item is considered dead stock.")

    def handle(self, *args, **options):
        self.days = max(1, options["days"])
        self.run_for_all_tenants()

    def handle_tenant(self, tenant):
        products = list(dead_stock_products(self.days))
        for product in products:
            notify(
                "dead_stock",
                f"{product.name} has {product.stock_on_hand or 0} unit(s) in stock with no movement for at least {self.days} days.",
                reference_id=str(product.id),
                dedupe_key=f"dead_stock:{product.id}:{self.days}:{timezone.localdate().isoformat()}",
            )
        self.stdout.write(self.style.SUCCESS(f"Created or refreshed {len(products)} dead-stock alert(s) for {tenant.schema_name}."))
