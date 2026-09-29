from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("audit", "0002_auditlogentry_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="auditlogentry", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
