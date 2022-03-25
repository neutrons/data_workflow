#!/bin/sh
set -e

# wait for postgress to be available
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# install things
make workflow

# start up things and echo the logs
cd /var/log
sleep 20
/opt/conda/bin/workflowmgr start
tail -F /var/log/workflow.log
