from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0002_idempotencykey_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="idempotencykey", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
