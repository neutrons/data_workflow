-- Index: dasmon_statusvariable_time_key
-- DROP INDEX dasmon_statusvariable_time_key;

CREATE INDEX dasmon_statusvariable_time_key
  ON dasmon_statusvariable
  USING btree
  (instrument_id_id , key_id_id , "timestamp" );
  
 