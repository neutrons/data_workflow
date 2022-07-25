#!/bin/sh
set -e

# wait for postgress to be available
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -d "${DATABASE_NAME}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "##################################\nPOSTGRES IS UP - executing command\n##################################"

# start test
webmonitor_pv_tester
