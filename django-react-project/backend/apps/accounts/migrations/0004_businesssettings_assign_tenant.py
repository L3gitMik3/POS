from django.db import migrations


def assign_current_schema(apps, schema_editor):
    Model = apps.get_model("accounts", "BusinessSettings")
    schema_name = getattr(schema_editor.connection, "schema_name", "public") or "public"
    Model.objects.using(schema_editor.connection.alias).all().update(tenant_schema=schema_name)


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_businesssettings_tenant_schema")]

    operations = [migrations.RunPython(assign_current_schema, migrations.RunPython.noop)]
