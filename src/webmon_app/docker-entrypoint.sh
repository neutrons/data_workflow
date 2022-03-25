#!/bin/sh
set -e

# wait for postgress to be available
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# install things
make webmon webmon/configure

# start up web-service
# entrypoint is python.package:function_name
gunicorn reporting.reporting_app.wsgi:application --preload --bind 0.0.0.0:8000
