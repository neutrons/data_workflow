-- Function used by DASMON to add PV entries

-- Function: "pvUpdate"(character varying, double precision, bigint, bigint)

DROP FUNCTION "pvUpdate"(character varying, double precision, bigint, bigint);

CREATE OR REPLACE FUNCTION "pvUpdate"(pv_name character varying, value double precision, status bigint, update_time bigint)
  RETURNS void AS
$BODY$
DECLARE
  n_count  numeric;
  n_id bigint;
BEGIN
  -- Create the parameter name entry if it doesn't already exist
  SELECT COUNT(*)
    FROM pvmon_pvname
    INTO n_count
    WHERE name = pv_name;

  IF n_count = 0 THEN
    INSERT INTO pvmon_pvname (name, monitored) VALUES (pv_name, true);
  END IF;

  -- Get the ID from the parameter name table
  SELECT id
    FROM pvmon_pvname
    INTO n_id
    WHERE name = pv_name;

  -- Add the entry for the new value
  INSERT INTO pvmon_pv (name_id, value, status, update_time)
    VALUES (n_id, value, status, update_time);
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION "pvUpdate"(character varying, double precision, bigint, bigint)
  OWNER TO postgres;

  
-- Function: "pvUpdate"(character varying, character varying, double precision, bigint, bigint)

DROP FUNCTION "pvUpdate"(character varying, character varying, double precision, bigint, bigint);

CREATE OR REPLACE FUNCTION "pvUpdate"(instrument character varying, pv_name character varying, value double precision, status bigint, update_time bigint)
  RETURNS void AS
$BODY$
DECLARE
  n_count  numeric;
  n_id bigint;
  n_instrument bigint;
BEGIN
  -- Create the parameter name entry if it doesn't already exist
  SELECT COUNT(*)
    FROM pvmon_pvname
    INTO n_count
    WHERE name = pv_name;

  IF n_count = 0 THEN
    INSERT INTO pvmon_pvname (name, monitored) VALUES (pv_name, true);
  END IF;

  -- Get the ID from the parameter name table
  SELECT id
    FROM pvmon_pvname
    INTO n_id
    WHERE name = pv_name;

  -- Get the instrument ID
  SELECT id
    FROM report_instrument
    INTO n_instrument
    WHERE name = lower(instrument);

  -- Add the entry for the new value
  INSERT INTO pvmon_pv (instrument_id, name_id, value, status, update_time)
    VALUES (n_instrument, n_id, value, status, update_time);
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION "pvUpdate"(character varying, character varying, double precision, bigint, bigint)
  OWNER TO postgres;
