from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("reporting", "0002_dailyreportsnapshot_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="dailyreportsnapshot", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
