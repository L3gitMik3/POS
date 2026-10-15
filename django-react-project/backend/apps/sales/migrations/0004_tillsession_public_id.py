import uuid

from django.db import migrations, models


def fill_public_ids(apps, schema_editor):
    TillSession = apps.get_model("sales", "TillSession")
    database = schema_editor.connection.alias
    session_ids = TillSession._base_manager.using(database).filter(public_id__isnull=True).values_list("pk", flat=True)
    for session_id in session_ids.iterator():
        TillSession._base_manager.using(database).filter(pk=session_id).update(public_id=uuid.uuid4())


class Migration(migrations.Migration):
    dependencies = [("sales", "0003_alter_tenant_schema_defaults")]

    operations = [
        migrations.AddField(
            model_name="tillsession",
            name="public_id",
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.RunPython(fill_public_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="tillsession",
            name="public_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
