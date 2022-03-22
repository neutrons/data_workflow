-- Index: report_runstatus_time_run
-- DROP INDEX report_runstatus_time_run;

CREATE INDEX report_runstatus_time_run
  ON report_runstatus
  USING btree
  (run_id_id , created_on );


-- Index: report_runstatus_time_id
-- DROP INDEX report_runstatus_time_id;

CREATE INDEX report_runstatus_time_id
  ON report_runstatus
  USING btree
  (id , created_on );
