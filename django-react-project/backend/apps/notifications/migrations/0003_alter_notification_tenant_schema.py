from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("notifications", "0002_notification_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="notification", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
