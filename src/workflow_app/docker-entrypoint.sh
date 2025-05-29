#!/bin/sh
set -e

# wait for postgress to be available
until python -c "import psycopg2; import os; psycopg2.connect(host=os.environ['DATABASE_HOST'], dbname=os.environ['DATABASE_NAME'], user=os.environ['DATABASE_USER'], password=os.environ['DATABASE_PASS']).close()"; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
>&2 echo "Postgres is up - executing command"

# install things
make install/workflow

# start up things and echo the logs
cd /var/log
sleep 20
/opt/conda/bin/workflowmgr start
tail -F /var/log/workflow.log
