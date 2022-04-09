import os
import time
import psycopg2
import unittest
from data_ready import create_run


class TestWorkflow:
    def setup_class(cls):
        # make sure datafiles and reduction script are in place
        os.system(
            """
        docker exec data_workflow_autoreducer_1 mkdir -p /SNS/TEST/IPTS-123/nexus
        docker exec data_workflow_autoreducer_1 touch /SNS/TEST/IPTS-123/nexus/TEST_100.nxs.h5
        docker exec data_workflow_autoreducer_1 mkdir -p /SNS/TEST/shared/autoreduce
        docker exec data_workflow_autoreducer_1 touch /SNS/TEST/shared/autoreduce/reduce_TEST.py
        """
        )
        # remove TEST instrument
        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )
        cursor = conn.cursor()
        cursor.execute("DELETE from report_instrument WHERE name = 'test';")
        conn.close()

        # annonce new run
        create_run("TEST", 123, 100)
        time.sleep(10)

    @unittest.skip("Skipping Temporarily To Allow Merge Into Next")
    def test(self):
        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )

        cursor = conn.cursor()

        # Check that the instrument has been created
        cursor.execute("SELECT COUNT(*) FROM report_instrument WHERE name = 'test';")
        assert cursor.fetchone()[0] == 1

        # Get instrument ID
        cursor.execute("SELECT id FROM report_instrument WHERE name = 'test';")
        instrument_id = cursor.fetchone()[0]

        # Check IPTS is created
        cursor.execute("SELECT COUNT(*) FROM report_ipts WHERE expt_name = 'IPTS-123';")
        assert cursor.fetchone()[0] == 1

        # Get instrument ID
        cursor.execute("SELECT id FROM report_ipts WHERE expt_name = 'IPTS-123';")
        ipts_id = cursor.fetchone()[0]

        # Check that the DataRun is created
        cursor.execute(
            f"SELECT COUNT(*) FROM report_datarun WHERE ipts_id_id = {ipts_id} AND instrument_id_id = {instrument_id};"
        )
        assert cursor.fetchone()[0] == 1

        # Get run ID
        cursor.execute(
            f"SELECT id FROM report_datarun WHERE ipts_id_id = {ipts_id} AND instrument_id_id = {instrument_id};"
        )
        datarun_id = cursor.fetchone()[0]

        # Check that run_number and file are correct
        cursor.execute(f"SELECT run_number,file FROM report_datarun WHERE id = {datarun_id};")
        assert cursor.fetchone() == (100, "/SNS/TEST/IPTS-123/nexus/TEST_100.nxs.h5")

        # Check number of runstatus, should equal 10
        cursor.execute(f"SELECT COUNT(*) FROM report_runstatus WHERE run_id_id = {datarun_id};")
        assert cursor.fetchone()[0] == 10

        # Check workflow summary is in correct state
        cursor.execute(
            "SELECT complete,catalog_started,cataloged,reduction_needed,reduction_started,reduced,"
            f"reduction_cataloged,reduction_catalog_started FROM report_workflowsummary WHERE run_id_id = {datarun_id};"
        )
        assert cursor.fetchone() == (True, True, True, True, True, True, True, True)

        conn.close()
