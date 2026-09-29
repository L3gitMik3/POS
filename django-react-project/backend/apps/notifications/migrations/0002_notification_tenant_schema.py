from django.db import migrations, models


def assign_current_schema(apps, schema_editor):
    Model = apps.get_model("notifications", "Notification")
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [("notifications", "0001_initial")]

    operations = [
        migrations.RemoveConstraint(model_name="notification", name="uniq_notification_dedupe_key"),
        migrations.AddField(model_name="notification", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.RunPython(assign_current_schema, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(condition=models.Q(dedupe_key__isnull=False), fields=("tenant_schema", "dedupe_key"), name="uniq_notification_dedupe_key"),
        ),
    ]
