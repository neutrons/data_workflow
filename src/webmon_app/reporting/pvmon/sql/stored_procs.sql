-- Function used by DASMON to add PV entries

-- Function: "pvUpdate"(character varying, double precision, bigint, bigint)

CREATE OR REPLACE FUNCTION pvUpdate(pv_name character varying, value double precision, status bigint, update_time bigint)
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
ALTER FUNCTION pvUpdate(character varying, double precision, bigint, bigint)
OWNER TO workflow;

-- Function: "pvUpdate"(character varying, character varying, double precision, bigint, bigint)

CREATE OR REPLACE FUNCTION pvUpdate(instrument character varying, pv_name character varying, value double precision, status bigint, update_time bigint)
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
ALTER FUNCTION pvUpdate(character varying, character varying, double precision, bigint, bigint)
OWNER TO workflow;

-- Function: "pvStringUpdate"(character varying, character varying, character varying, bigint, bigint)

CREATE OR REPLACE FUNCTION pvStringUpdate(instrument character varying, pv_name character varying, value character varying, status bigint, update_time bigint)
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
ALTER FUNCTION pvStringUpdate(character varying, character varying, character varying, bigint, bigint)
  OWNER TO workflow;

-- Function: "setInstrumentPVs"(character varying, text[])

CREATE OR REPLACE FUNCTION setInstrumentPVs(instrument character varying, pvs text[])
RETURNS void AS $$
DECLARE
    n_instrument bigint;
    n_pv_id bigint;
    n_pv_name character varying;
    n_count integer;
BEGIN
    -- Get the ID of the instrument
    SELECT id
      INTO n_instrument
      FROM report_instrument
      WHERE name = lower(instrument);

    -- Make sure the instrument exists
    IF n_instrument IS NULL THEN
        RAISE EXCEPTION 'Instrument % does not exist', instrument;
    END IF;

    -- Delete the existing monitored variables for this instrument
    DELETE
    FROM pvmon_monitoredvariable
    WHERE instrument_id = n_instrument;

    -- Insert the new monitored variables without duplicates
    FOREACH n_pv_name IN ARRAY pvs
    LOOP
        SELECT id INTO n_pv_id FROM pvmon_pvname WHERE name = n_pv_name;
        IF n_pv_id IS NOT NULL THEN
            INSERT INTO pvmon_monitoredvariable (instrument_id, pv_name_id, rule_name)
              SELECT pvmon_pv.instrument_id, pvmon_pv.name_id, ''
              FROM pvmon_pv
              WHERE pvmon_pv.instrument_id=n_instrument AND pvmon_pv.name_id = n_pv_id
              LIMIT 1;
        END IF;
    END LOOP;
    SELECT count(*)
      INTO n_count
      FROM pvmon_monitoredvariable;
    IF n_count = 0 THEN
      INSERT INTO pvmon_monitoredvariable (instrument_id, rule_name)
      VALUES (n_instrument, '');
    END IF;
END;
$$ LANGUAGE plpgsql VOLATILE
  COST 100;

ALTER FUNCTION setInstrumentPVs(character varying, text[])
  OWNER TO workflow;
