from django.db import migrations, models


def assign_current_schema(apps, schema_editor):
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    for model_name in ("Supplier", "PurchaseOrder", "PurchaseOrderLine", "GoodsReceivedNote", "GRNLine"):
        Model = apps.get_model("purchasing", model_name)
        Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [("purchasing", "0001_initial")]

    operations = [
        migrations.AddField(model_name="supplier", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="purchaseorder", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="purchaseorderline", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="goodsreceivednote", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.AddField(model_name="grnline", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.RunPython(assign_current_schema, migrations.RunPython.noop),
    ]
