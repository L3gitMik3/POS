from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_businesssettings_assign_tenant")]

    operations = [
        migrations.AlterField(
            model_name="businesssettings",
            name="tenant_schema",
            field=models.CharField(blank=True, db_index=True, default="", max_length=63),
        ),
    ]
