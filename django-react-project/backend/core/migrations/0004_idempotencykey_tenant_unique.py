from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0003_alter_idempotencykey_tenant_schema")]

    operations = [
        migrations.AlterField(
            model_name="idempotencykey",
            name="key",
            field=models.CharField(db_index=True, max_length=255),
        ),
        migrations.AddConstraint(
            model_name="idempotencykey",
            constraint=models.UniqueConstraint(fields=("tenant_schema", "key"), name="uniq_idempotency_key_per_tenant"),
        ),
    ]
