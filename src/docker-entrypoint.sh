#!/bin/sh
set -e
  
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
  
>&2 echo "Postgres is up - executing command"

if [ ! -f /tmp/installed ]; then
  make install
  touch /tmp/installed
fi
cd ${SETTINGS_DIR}

gunicorn reporting_app.wsgi:application --bind 0.0.0.0:8000