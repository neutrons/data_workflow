#!/bin/bash
set -e

# wait for postgres to be available
until python -c "import psycopg2; import os; psycopg2.connect(host=os.environ['DATABASE_HOST'], dbname=os.environ['DATABASE_NAME'], user=os.environ['DATABASE_USER'], password=os.environ['DATABASE_PASS']).close()"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# configure the application (pip install done at Docker build time; django-admin is on PATH
# because this entrypoint runs inside 'pixi run -e webmon' via the container CMD)
django-admin collectstatic --noinput
django-admin makemigrations --noinput
django-admin migrate --fake-initial --noinput
django-admin migrate --run-syncdb --noinput
django-admin createcachetable webcache
django-admin ensure_adminuser --username="${DATABASE_USER}" --email='workflow@example.com' --password="${DATABASE_PASS}"
django-admin add_stored_procs
django-admin add_indices

# add test users if not in prod
>&2 echo "Checking if in prod..."
if [[ "$DJANGO_SETTINGS_MODULE" != *".prod" ]]; then
  if [[ "${LOAD_INITIAL_DATA}" = "true" ]]; then
    django-admin loaddata "$(python -c "import reporting, os; print(os.path.join(os.path.dirname(reporting.__file__), 'fixtures', 'db_init.json'))")"
  fi
  if [ -z "$GENERAL_USER_USERNAME" ]; then
    GENERAL_USER_USERNAME="GeneralUser"
    GENERAL_USER_PASSWORD="GeneralUser"
  fi
  >&2 echo "Not in production — creating test users InstrumentScientist and GeneralUser"
  django-admin ensure_adminuser --username="InstrumentScientist" --email='Instrument@Scientist.com' --password="InstrumentScientist"
  django-admin ensure_user --username="${GENERAL_USER_USERNAME}" --email='General@User.com' --password="${GENERAL_USER_PASSWORD}"
  >&2 echo "Not in production — updating certificates to add self-signed certificate"
  update-ca-certificates
fi

# start up web-service
# entrypoint is python.package:function_name
# additional command-line arguments via environment variable GUNICORN_CMD_ARGS
gunicorn reporting.reporting_app.wsgi:application --bind 0.0.0.0:8000
