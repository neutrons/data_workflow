-- Function used by DASMON to add PV entries

-- Function: "pvUpdate"(character varying, double precision, bigint, bigint)

DROP FUNCTION "pvUpdate"(character varying, double precision, bigint, bigint);

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

  
-- Function: "pvUpdate"(character varying, character varying, double precision, bigint, bigint)

DROP FUNCTION "pvUpdate"(character varying, character varying, double precision, bigint, bigint);

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

  
-- Function: "pvStringUpdate"(character varying, character varying, character varying, bigint, bigint)

DROP FUNCTION "pvStringUpdate"(character varying, character varying, character varying, bigint, bigint);

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