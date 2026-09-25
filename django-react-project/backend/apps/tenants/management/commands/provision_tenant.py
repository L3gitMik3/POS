from django.core.management.base import BaseCommand

from apps.tenants.services import provision_tenant


class Command(BaseCommand):
    help = "Provision a tenant schema"

    def handle(self, *args, **options):
        provision_tenant(slug="demo", name="Demo Tenant", owner_username="owner", owner_password="password")
        self.stdout.write(self.style.SUCCESS("Tenant provision command ready"))
