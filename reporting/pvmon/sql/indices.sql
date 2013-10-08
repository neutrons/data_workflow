-- Index: pvmon_pv_time_key
-- DROP INDEX pvmon_pv_time_key;

CREATE INDEX pvmon_pv_time_key
  ON pvmon_pv
  USING btree
  (instrument_id , name_id , update_time );