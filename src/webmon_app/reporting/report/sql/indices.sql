-- Index: report_runstatus_time_run
-- DROP INDEX report_runstatus_time_run;

CREATE INDEX IF NOT EXISTS report_runstatus_time_run
  ON report_runstatus
  USING btree
  (run_id_id , created_on );


-- Index: report_runstatus_time_id
-- DROP INDEX report_runstatus_time_id;

CREATE INDEX IF NOT EXISTS report_runstatus_time_id
  ON report_runstatus
  USING btree
  (id , created_on );


CREATE INDEX IF NOT EXISTS report_runstatus_created_on
  ON report_runstatus
  USING btree
  (created_on);

CREATE INDEX IF NOT EXISTS report_datarun_created_on
  ON report_datarun
  USING btree
  (created_on);
