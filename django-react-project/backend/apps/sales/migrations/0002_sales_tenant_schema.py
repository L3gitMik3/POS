from django.conf import settings
from django.db import migrations, models


def assign_current_schema(apps, schema_editor):
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    for model_name in ("Customer", "LoyaltyRule", "Return", "ReturnLine", "Sale", "SaleLine", "TillSession"):
        Model = apps.get_model("sales", model_name)
        Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [
        ("sales", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(model_name="customer", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="loyaltyrule", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="return", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="returnline", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="sale", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="saleline", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="tillsession", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.RunPython(assign_current_schema, migrations.RunPython.noop),
        migrations.AlterField(model_name="customer", name="phone_number", field=models.CharField(max_length=50)),
        migrations.AlterField(model_name="sale", name="client_uuid", field=models.UUIDField(blank=True, null=True)),
        migrations.AlterField(model_name="sale", name="receipt_number", field=models.CharField(max_length=50)),
        migrations.AddConstraint(model_name="customer", constraint=models.UniqueConstraint(fields=("tenant_schema", "phone_number"), name="uniq_customer_phone_per_tenant")),
        migrations.AddConstraint(model_name="sale", constraint=models.UniqueConstraint(fields=("tenant_schema", "receipt_number"), name="uniq_receipt_per_tenant")),
        migrations.AddConstraint(model_name="sale", constraint=models.UniqueConstraint(condition=models.Q(client_uuid__isnull=False), fields=("tenant_schema", "client_uuid"), name="uniq_sale_client_uuid_per_tenant")),
    ]
