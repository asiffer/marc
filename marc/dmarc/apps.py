import sys

from django.apps import AppConfig
from django.db.backends.signals import connection_created
from django.db.backends.sqlite3.base import DatabaseWrapper


def display_database_location(*args, connection: DatabaseWrapper, **kwargs):
    print("Database located at", connection.get_connection_params().get("database", ""))


class DmarcConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "marc.dmarc"

    def ready(self) -> None:
        if "runserver" in sys.argv:
            connection_created.connect(display_database_location)
        return super().ready()
