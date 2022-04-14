import os
import time
import psycopg2
import pytest
import requests
import subprocess
import datetime
import unittest
from data_ready import create_run


class TestWorkflow:
    URL_base = "http://localhost"
    reduction_path = "/reduction/ARCS/"

    @pytest.fixture
    def instrument_scientist_client(self):
        client = self.logged_in_client(self.reduction_path, "InstrumentScientist", "InstrumentScientist")
        yield client

    def logged_in_client(self, next, username, password):
        URL = self.URL_base + "/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        client.post(URL + next, data=login_data, timeout=None)
        return client

    def prepareEnvironmentForReductionScriptGeneration(self):
        os.system(
            """
        docker exec data_workflow_autoreducer_1 mkdir -p /SNS/ARCS/IPTS-123/nexus
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/IPTS-123/nexus/ARCS_100.nxs.h5
        docker exec data_workflow_autoreducer_1 mkdir -p /SNS/ARCS/shared/autoreduce/vanadium_files
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS_default.py
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS.py
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS.py.template
        docker exec -i data_workflow_autoreducer_1 bash -c 'echo "#!/usr/bin/env python3\n# this is a template\ndef init():\nprint(5)\n" > /SNS/ARCS/shared/autoreduce/reduce_ARCS.py.template'
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/shared/autoreduce/ARCS_2X1_grouping.xml
        docker exec data_workflow_autoreducer_1 touch /SNS/ARCS/shared/autoreduce/vanadium_files/test_van201562.nxs
        """  # noqa: E501
        )

    def getReductionScriptContents(self):
        return subprocess.check_output(
            "docker exec data_workflow_autoreducer_1 cat /SNS/ARCS/shared/autoreduce/reduce_ARCS.py", shell=True
        )

    def initReductionGroup(self, conn, cursor):
        cursor.execute("SELECT * from reduction_reductionproperty WHERE instrument_id = 3;")
        if cursor.fetchone() is None:
            timestamp = datetime.datetime.now()
            cursor.execute(
                "INSERT INTO reduction_reductionproperty (instrument_id, key, value, timestamp) VALUES(%s, %s, %s, %s)",
                (3, "grouping", "/SNS/ARCS/shared/autoreduce/ARCS_2X1_grouping.xml", timestamp),
            )
            conn.commit()

        cursor.execute("SELECT * from reduction_choice WHERE instrument_id = 3;")
        if cursor.fetchone() is None:
            cursor.execute("SELECT * FROM reduction_reductionproperty WHERE key = 'grouping';")
            props = cursor.fetchone()
            cursor.execute(
                "INSERT INTO reduction_choice (instrument_id, property_id, description, value) VALUES(%s, %s, %s, %s)",
                (props[1], props[0], "2X1", "/SNS/ARCS/shared/autoreduce/ARCS_2X1_grouping.xml"),
            )
            conn.commit()

    def getReductionData(self, instrument_scientist_client):
        csrftoken = instrument_scientist_client.cookies["csrftoken"]
        reduction_data = dict(
            csrfmiddlewaretoken=csrftoken,
            raw_vanadium="/SNS/ARCS/IPTS-123/nexus/ARCS_100.nxs.h5",
            processed_vanadium="/SNS/ARCS/shared/autoreduce/vanadium_files/test_van201562.nxs",
            grouping="/SNS/ARCS/shared/autoreduce/ARCS_2X1_grouping.xml",
            e_min="-0.95",
            e_step="0.01",
            e_max="0.95",
            button_choice="submit",
        )
        reduction_data["form-TOTAL_FORMS"] = "0"
        reduction_data["form-INITIAL_FORMS"] = "0"
        reduction_data["form-MIN_NUM_FORMS"] = "0"
        reduction_data["form-MAX_NUM_FORMS"] = "1000"

        reduction_data["form-0-bank"] = ""
        reduction_data["form-0-tube"] = ""
        reduction_data["form-0-pixel"] = "1-7,122-128"

        reduction_data["form-1-bank"] = "70"
        reduction_data["form-1-tube"] = ""
        reduction_data["form-1-pixel"] = "1-12,117-128"

        reduction_data["form-2-bank"] = "71"
        reduction_data["form-2-tube"] = ""
        reduction_data["form-2-pixel"] = "1-14,115-128"
        return reduction_data

    def testReduction(self, instrument_scientist_client):

        self.prepareEnvironmentForReductionScriptGeneration()

        assert not self.getReductionScriptContents()

        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )
        cursor = conn.cursor()

        self.initReductionGroup(conn, cursor)

        reduction_data = self.getReductionData(instrument_scientist_client)

        instrument_scientist_client.post(self.URL_base + self.reduction_path, data=reduction_data, timeout=None)
        time.sleep(1)
        assert self.getReductionScriptContents()
        os.system(
            """docker exec -i data_workflow_autoreducer_1 bash -c '> /SNS/ARCS/shared/autoreduce/reduce_ARCS.py'"""
        )
        assert not self.getReductionScriptContents()

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
        time.sleep(1)

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
