#!/bin/bash

echo "Retrieving schema from mysql."
mysqldump --host=mac83808.ornl.gov --user=icat --password=icat --no-data reporting_db --compatible=postgresql > reporting_db-schema-mysql.sql

echo "Automated conversion"
perl my2pg.pl <reporting_db-schema-mysql.sql > reporting_db-schema-postgresql.sql

echo "Now you need to manually remove all CONSTRAINT clauses and just leave the PRIMARY KEY.  Also add the comma after the primary key"
echo "In addition you will need to reorder those so the tables are created before attempting to use as a foreign key"
echo "Edit the file reporting_db-schema-postgresql.sql.  Have fun editing!"

