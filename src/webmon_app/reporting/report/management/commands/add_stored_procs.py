# flake8: noqa: F401
from django.core.management.base import BaseCommand
from django.db import connection
from pathlib import Path


def _parse_sql_file(filename):
    """Read in an sql file full of stored proceedures and return as a list"""
    if not filename.exists():
        raise RuntimeError(f"Failed to find '{filename.name}' in '{filename.parent}'")

    with open(filename, "r") as handle:
        everything = handle.read()  # whole file into single string

    # split file into sections based on tags
    TAG = "-- Function: "
    functions = [TAG + stuff for stuff in everything.split(TAG) if stuff.strip()]  # remove empty parts
    # remove "empty" functions
    # there is some boilerplate at the top of one of the sql scripts
    functions = [stuff for stuff in functions if len(stuff.split("\n")) > 3]
    return functions


# error_rate and run_rate are taken from report/sql/stored_procs.sql
filename = Path(__file__).resolve(strict=True).parent.parent.parent / "sql" / "stored_procs.sql"
error_rate_sql, run_rate_sql = _parse_sql_file(filename)

# pv_update, pv_update2, are taken from pvmon/sql/stored_procs.sql
filename = Path(__file__).resolve(strict=True).parent.parent.parent.parent / "pvmon" / "sql" / "stored_procs.sql"
pv_update_sql, pv_update2_sql, pvstring_update_sql = _parse_sql_file(filename)


class Command(BaseCommand):
    help = "add additional stored procedures to backend database"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # report/sql/stored_proces.sql
            cursor.execute(error_rate_sql)
            cursor.execute(run_rate_sql)
            # pvmon/sql/stored_proces.sql
            cursor.execute(pv_update_sql)
            cursor.execute(pv_update2_sql)
            cursor.execute(pvstring_update_sql)
