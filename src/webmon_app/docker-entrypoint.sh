#!/bin/sh
set -e

MANAGE_PY_WEBMON="/opt/conda/lib/python3.7/site-packages/reporting/manage.py"

# wait for postgress to be available
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# install things
make install/webmon configure/webmon

# add test users if not in prod
>&2 echo "\n\nChecking if in prod...\n\n"
if ! (".prod" in $DJANGO_SETTINGS_MODULE); then
  if [ -z "$GENERAL_USER_USERNAME"]; then
    GENERAL_USER_USERNAME="GeneralUser"
    GENERAL_USER_PASSWORD="GeneralUser"
  fi
  >&2 echo "Not in Production, setting up test users InstrumentScientist, and GeneralUser"
  python $MANAGE_PY_WEBMON ensure_adminuser --username="InstrumentScientist" --email='Instrument@Scientist.com' --password="InstrumentScientist"
  python $MANAGE_PY_WEBMON ensure_user --username="${GENERAL_USER_USERNAME}" --email='General@User.com' --password="${GENERAL_USER_PASSWORD}"
fi

# start up web-service
# entrypoint is python.package:function_name
gunicorn reporting.reporting_app.wsgi:application --preload --bind 0.0.0.0:8000
