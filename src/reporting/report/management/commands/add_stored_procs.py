# flake8: noqa: F401
from django.core.management.base import BaseCommand
from django.db import connection


# error_rate and run_rate are taken from report/sql/stored_procs.sql
error_rate_sql = """
CREATE OR REPLACE FUNCTION error_rate(instrument_id bigint)
RETURNS refcursor AS
$BODY$DECLARE
ref refcursor;
BEGIN
OPEN ref FOR
SELECT MAX(TIMESTAMP) AS TIME, COUNT(*)
FROM report_error t
    INNER JOIN (
    SELECT 
        TRUNC(EXTRACT(EPOCH FROM report_runstatus.created_on-LOCALTIMESTAMP)/3600) AS TIMESTAMP, report_error.id
    FROM report_error
    INNER JOIN report_runstatus
    ON report_error.run_status_id_id=report_runstatus.id
    INNER JOIN report_datarun
    ON report_runstatus.run_id_id=report_datarun.id
    WHERE
        (report_datarun.instrument_id_id = instrument_id AND 
        report_runstatus.created_on >= LOCALTIMESTAMP-INTERVAL '1 DAY')
    ) m ON t.id = m.id
    GROUP BY timestamp;
RETURN ref;
END
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION error_rate(bigint)
OWNER TO postgres;
"""

run_rate_sql = """
CREATE OR REPLACE FUNCTION run_rate(instrument_id bigint)
RETURNS refcursor AS
$BODY$
DECLARE
ref refcursor;
BEGIN
OPEN ref FOR
SELECT MAX(TIMESTAMP) AS TIME, COUNT(*)
FROM report_datarun t
    INNER JOIN (
    SELECT 
        TRUNC(EXTRACT(EPOCH FROM report_datarun.created_on-LOCALTIMESTAMP)/3600) AS TIMESTAMP, report_datarun.id
    FROM report_datarun 
    WHERE 
        (report_datarun.instrument_id_id = instrument_id AND report_datarun.created_on >= LOCALTIMESTAMP-INTERVAL '1 DAY' )
    ) m ON t.id = m.id
    GROUP BY timestamp;
RETURN ref;
END;$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION run_rate(bigint)
OWNER TO postgres;
"""

# pv_update, pv_update2, are taken from pvmon/sql/stored_procs.sql
pv_update_sql = """
CREATE OR REPLACE FUNCTION "pvUpdate"(pv_name character varying, value double precision, status bigint, update_time bigint)
RETURNS void AS
$BODY$DECLARE
n_count numeric;
n_id bigint;
new_value double precision;
new_time bigint;
BEGIN
new_value := value;
new_time := update_time;
-- Create the parameter name entry if it doesn't already exist
SELECT COUNT(*)
    FROM pvmon_pvname
    INTO n_count
    WHERE pvmon_pvname.name = pv_name;
IF n_count = 0 THEN
    INSERT INTO pvmon_pvname (name, monitored) VALUES (pv_name, true);
END IF;
-- Get the ID from the parameter name table
SELECT id
    FROM pvmon_pvname
    INTO n_id
    WHERE pvmon_pvname.name = pv_name;
-- Add the entry for the new value
INSERT INTO pvmon_pv (name_id, value, status, update_time)
    VALUES (n_id, new_value, status, update_time);
-- Cache the latest values
SELECT COUNT(*)
    FROM pvmon_pvcache
    INTO n_count
    WHERE pvmon_pvcache.name_id = n_id;
IF n_count = 0 THEN
    INSERT INTO pvmon_pvcache (name_id, value, status, update_time)
    VALUES (n_id, value, status, update_time);
ELSE
    UPDATE pvmon_pvcache
    SET value=new_value, update_time=new_time
    WHERE name_id = n_id;
END IF;
END;$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION "pvUpdate"(character varying, double precision, bigint, bigint)
OWNER TO postgres;
"""

pv_update2_sql = """
CREATE OR REPLACE FUNCTION "pvUpdate"(instrument character varying, pv_name character varying, value double precision, status bigint, update_time bigint)
RETURNS void AS
$BODY$
DECLARE
n_count  numeric;
n_id bigint;
n_instrument bigint;
new_value double precision;
new_time bigint;
BEGIN
new_value := value;
new_time := update_time;
-- Create the parameter name entry if it doesn't already exist
SELECT COUNT(*)
    FROM pvmon_pvname
    INTO n_count
    WHERE pvmon_pvname.name = pv_name;
IF n_count = 0 THEN
    INSERT INTO pvmon_pvname (name, monitored) VALUES (pv_name, true);
END IF;
-- Get the ID from the parameter name table
SELECT id
    FROM pvmon_pvname
    INTO n_id
    WHERE pvmon_pvname.name = pv_name;
-- Get the instrument ID
SELECT id
    FROM report_instrument
    INTO n_instrument
    WHERE report_instrument.name = lower(instrument);
-- Add the entry for the new value
INSERT INTO pvmon_pv (instrument_id, name_id, value, status, update_time)
    VALUES (n_instrument, n_id, new_value, status, new_time);
-- Cache the latest values
SELECT COUNT(*)
    FROM pvmon_pvcache
    INTO n_count
    WHERE pvmon_pvcache.instrument_id=n_instrument AND pvmon_pvcache.name_id = n_id;
IF n_count = 0 THEN
    INSERT INTO pvmon_pvcache (instrument_id, name_id, value, status, update_time)
    VALUES (n_instrument, n_id, new_value, status, new_time);
ELSE
    UPDATE pvmon_pvcache
    SET value=new_value, update_time=new_time
    WHERE name_id = n_id AND instrument_id = n_instrument;
END IF;
END;
$BODY$
LANGUAGE plpgsql VOLATILE
COST 100;
ALTER FUNCTION "pvUpdate"(character varying, character varying, double precision, bigint, bigint)
OWNER TO postgres;
"""

pvstring_update_sql = """
CREATE OR REPLACE FUNCTION "pvStringUpdate"(instrument character varying, pv_name character varying, value character varying, status bigint, update_time bigint)
  RETURNS void AS
$BODY$
DECLARE
  n_count  numeric;
  n_id bigint;
  n_instrument bigint;
  new_value character varying;
  new_time bigint;
BEGIN
  new_value := value;
  new_time := update_time;
  -- Create the parameter name entry if it doesn't already exist
  SELECT COUNT(*)
    FROM pvmon_pvname
    INTO n_count
    WHERE pvmon_pvname.name = pv_name;
  IF n_count = 0 THEN
    INSERT INTO pvmon_pvname (name, monitored) VALUES (pv_name, true);
  END IF;
  -- Get the ID from the parameter name table
  SELECT id
    FROM pvmon_pvname
    INTO n_id
    WHERE pvmon_pvname.name = pv_name;
  -- Get the instrument ID
  SELECT id
    FROM report_instrument
    INTO n_instrument
    WHERE report_instrument.name = lower(instrument);
  -- Add the entry for the new value
  INSERT INTO pvmon_pvstring (instrument_id, name_id, value, status, update_time)
    VALUES (n_instrument, n_id, new_value, status, new_time);
  -- Cache the latest values
  SELECT COUNT(*)
    FROM pvmon_pvstringcache
    INTO n_count
    WHERE pvmon_pvstringcache.instrument_id=n_instrument AND pvmon_pvstringcache.name_id = n_id;
  IF n_count = 0 THEN
    INSERT INTO pvmon_pvstringcache (instrument_id, name_id, value, status, update_time)
      VALUES (n_instrument, n_id, new_value, status, new_time);
  ELSE
    UPDATE pvmon_pvstringcache
      SET value=new_value, update_time=new_time
      WHERE name_id = n_id AND instrument_id = n_instrument;
  END IF;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION "pvStringUpdate"(character varying, character varying, character varying, bigint, bigint)
  OWNER TO postgres;
"""


class Command(BaseCommand):
    help = "add additional stored procedures to backend database"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # report/sql/stored_proces.sql
            cursor.execute(error_rate_sql)
            cursor.execute(run_rate_sql)
            # pvmon/sql/stored_proces.sql
            cursor.execute(pv_update_sql)
            cursor.execute(pv_update2_sql)
            cursor.execute(pvstring_update_sql)
