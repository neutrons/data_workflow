# flake8: noqa: F401
from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path

# from report/sql/indices.sql
report_indices = Path(__file__).resolve(strict=True).parent.parent.parent / "sql" / "indices.sql"

# from pvmon/sql/indices.sql
pvmon_indices = Path(__file__).resolve(strict=True).parent.parent.parent.parent / "pvmon" / "sql" / "indices.sql"

# from dasmon/sql/indices.sql
dasmon_indices = Path(__file__).resolve(strict=True).parent.parent.parent.parent / "dasmon" / "sql" / "indices.sql"


class Command(BaseCommand):
    help = "add additional indexes to backend database"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute(open(report_indices).read())
            cursor.execute(open(pvmon_indices).read())
            cursor.execute(open(dasmon_indices).read())
