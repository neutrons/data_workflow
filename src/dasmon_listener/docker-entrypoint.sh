#!/bin/sh
set -e
  
until PGPASSWORD=${DATABASE_PASS} psql -h "${DATABASE_HOST}" -U "${DATABASE_USER}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done
  
>&2 echo "Postgres is up - executing command"

if [ ! -f /tmp/installed ]; then
  make dasmonlistener
  touch /tmp/installed
fi
cd /var/log
/usr/bin/dasmon_listener start && tail -F /var/log/dasmon_listener.log