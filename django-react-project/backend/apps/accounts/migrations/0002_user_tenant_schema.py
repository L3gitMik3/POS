from django.db import migrations, models
from django.utils.text import slugify


def assign_existing_users_to_tenants(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Tenant = apps.get_model("tenants", "Tenant")
    tenants_by_schema = {tenant.schema_name: tenant.schema_name for tenant in Tenant.objects.all()}

    for user in User.objects.filter(tenant_schema="").iterator():
        schema_name = slugify(user.full_name).replace("-", "_")
        if schema_name in tenants_by_schema:
            user.tenant_schema = tenants_by_schema[schema_name]
            user.save(update_fields=["tenant_schema"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("tenants", "0002_tenant_business_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="tenant_schema",
            field=models.CharField(blank=True, default="", max_length=63),
        ),
        migrations.RunPython(assign_existing_users_to_tenants, migrations.RunPython.noop),
    ]
