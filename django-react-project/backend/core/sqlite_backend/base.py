from django.db.backends.sqlite3.base import DatabaseWrapper as SQLiteDatabaseWrapper


class DatabaseWrapper(SQLiteDatabaseWrapper):
    schema_name = "public"

    def set_schema(self, schema_name, include_public=True, **kwargs):
        self.schema_name = schema_name

    def set_schema_to_public(self):
        self.schema_name = "public"
