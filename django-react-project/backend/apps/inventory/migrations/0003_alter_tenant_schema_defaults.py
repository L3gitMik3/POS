from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inventory", "0002_category_tenant_schema_product_tenant_schema_and_more")]

    operations = [
        migrations.AlterField(model_name="category", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="product", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="stockmovement", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
