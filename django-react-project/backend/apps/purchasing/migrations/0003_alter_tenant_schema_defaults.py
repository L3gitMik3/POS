from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("purchasing", "0002_purchasing_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="goodsreceivednote", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="grnline", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="purchaseorder", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="purchaseorderline", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="supplier", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
