from django.db import migrations, models


def assign_current_schema(apps, schema_editor):
    Model = apps.get_model("reporting", "DailyReportSnapshot")
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [("reporting", "0001_initial")]

    operations = [
        migrations.AddField(model_name="dailyreportsnapshot", name="tenant_schema", field=models.CharField(db_index=True, default="public", max_length=63)),
        migrations.RunPython(assign_current_schema, migrations.RunPython.noop),
        migrations.AlterField(model_name="dailyreportsnapshot", name="date", field=models.DateField()),
        migrations.AddConstraint(model_name="dailyreportsnapshot", constraint=models.UniqueConstraint(fields=("tenant_schema", "date"), name="uniq_daily_snapshot_per_tenant")),
    ]
