-- Function: error_rate(bigint)

-- DROP FUNCTION error_rate(bigint);

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

-- Function: run_rate(bigint)

-- DROP FUNCTION run_rate(bigint);

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

