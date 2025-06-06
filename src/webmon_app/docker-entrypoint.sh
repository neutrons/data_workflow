#!/bin/bash
set -e

MANAGE_PY_WEBMON="/opt/conda/lib/python3.11/site-packages/reporting/manage.py"

# wait for postgress to be available
until python -c "import psycopg2; import os; psycopg2.connect(host=os.environ['DATABASE_HOST'], dbname=os.environ['DATABASE_NAME'], user=os.environ['DATABASE_USER'], password=os.environ['DATABASE_PASS']).close()"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# install things
make install/webmon configure/webmon

# add test users if not in prod
>&2 echo "\n\nChecking if in prod...\n\n"
if [[ "$DJANGO_SETTINGS_MODULE" != *".prod" ]]; then
  if [[ "${LOAD_INITIAL_DATA}" = "true" ]]; then
    make configure/load_initial_data
  fi
  if [ -z "$GENERAL_USER_USERNAME"]; then
    GENERAL_USER_USERNAME="GeneralUser"
    GENERAL_USER_PASSWORD="GeneralUser"
  fi
  >&2 echo "Not in Production, setting up test users InstrumentScientist, and GeneralUser"
  python $MANAGE_PY_WEBMON ensure_adminuser --username="InstrumentScientist" --email='Instrument@Scientist.com' --password="InstrumentScientist"
  python $MANAGE_PY_WEBMON ensure_user --username="${GENERAL_USER_USERNAME}" --email='General@User.com' --password="${GENERAL_USER_PASSWORD}"
  >&2 echo "Not in Production, updating certificates to add self-signed certificate"
  update-ca-certificates
fi

# start up web-service
# entrypoint is python.package:function_name
# additional command-line arguments via environment variable GUNICORN_CMD_ARGS
gunicorn reporting.reporting_app.wsgi:application --bind 0.0.0.0:8000
