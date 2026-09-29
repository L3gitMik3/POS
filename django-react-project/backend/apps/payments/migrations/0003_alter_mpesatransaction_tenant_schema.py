from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("payments", "0002_mpesatransaction_tenant_schema")]

    operations = [
        migrations.AlterField(model_name="mpesatransaction", name="tenant_schema", field=models.CharField(blank=True, db_index=True, default="", max_length=63)),
    ]
