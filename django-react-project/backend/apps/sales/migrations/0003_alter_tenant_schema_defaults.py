from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("sales", "0002_sales_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="customer", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="loyaltyrule", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="return", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="returnline", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="sale", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="saleline", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
        migrations.AlterField(model_name="tillsession", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
