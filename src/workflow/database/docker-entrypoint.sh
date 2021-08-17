#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username $DATABASE_USER --dbname $DATABASE_NAME <<-EOSQL
    CREATE USER $AMQDB_USER;
    CREATE DATABASE $AMQDB_NAME OWNER $AMQDB_USER;
    GRANT ALL PRIVILEGES ON DATABASE $AMQDB_NAME TO $AMQDB_USER;
EOSQL

echo 'host	workflow 	workflow	128.219.164.181/32	md5' >> /var/lib/postgresql/data/pgdata/pg_hba.conf
echo 'host	workflow 	workflow	128.219.164.209/32	md5' >> /var/lib/postgresql/data/pgdata/pg_hba.conf
