#!/bin/sh
set -e
  
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
  
>&2 echo "Postgres is up - executing command"

make install
cd ${SETTINGS_DIR}
python manage.py runserver 0.0.0.0:8000
