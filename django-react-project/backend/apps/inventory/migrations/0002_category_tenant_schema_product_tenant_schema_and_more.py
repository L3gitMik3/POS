from django.db import migrations, models


def assign_current_schema(apps, schema_editor):
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    for model_name in ("Category", "Product", "StockMovement"):
        Model = apps.get_model("inventory", model_name)
        Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [("inventory", "0001_initial")]

    operations = [
        migrations.AddField(model_name="category", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="product", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="stockmovement", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.RunPython(assign_current_schema, migrations.RunPython.noop),
        migrations.AlterField(model_name="product", name="barcode", field=models.CharField(blank=True, max_length=100, null=True)),
        migrations.AlterField(model_name="product", name="sku", field=models.CharField(max_length=100)),
        migrations.AddConstraint(model_name="product", constraint=models.UniqueConstraint(fields=("tenant_schema", "sku"), name="uniq_product_sku_per_tenant")),
        migrations.AddConstraint(model_name="product", constraint=models.UniqueConstraint(fields=("tenant_schema", "barcode"), name="uniq_product_barcode_per_tenant")),
    ]
