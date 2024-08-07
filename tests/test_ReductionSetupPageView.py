import os
import time
import psycopg2
import pytest
import requests
import subprocess
import datetime


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
        docker exec data_workflow-autoreducer-1 mkdir -p /SNS/ARCS/IPTS-123/nexus
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/IPTS-123/nexus/ARCS_100.nxs.h5
        docker exec data_workflow-autoreducer-1 mkdir -p /SNS/ARCS/shared/autoreduce/vanadium_files
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS_default.py
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS.py
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/shared/autoreduce/reduce_ARCS.py.template
        docker exec -i data_workflow-autoreducer-1 bash -c 'echo "#!/usr/bin/env python3\n# this is a template\ndef init():\nprint(5)\n" > /SNS/ARCS/shared/autoreduce/reduce_ARCS.py.template'
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/shared/autoreduce/ARCS_2X1_grouping.xml
        docker exec data_workflow-autoreducer-1 touch /SNS/ARCS/shared/autoreduce/vanadium_files/test_van201562.nxs
        """  # noqa: E501
        )

    def getReductionScriptContents(self):
        return subprocess.check_output(
            "docker exec data_workflow-autoreducer-1 cat /SNS/ARCS/shared/autoreduce/reduce_ARCS.py", shell=True
        ).decode()

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
        # backup reduce_ARCS.py
        os.system(
            """docker exec -i data_workflow-autoreducer-1 bash -c \
            'cp /SNS/ARCS/shared/autoreduce/reduce_ARCS.py /tmp/reduce_ARCS.py'"""
        )
        self.prepareEnvironmentForReductionScriptGeneration()

        assert "this is a template" not in self.getReductionScriptContents()

        conn = psycopg2.connect(
            database="workflow",
            user="workflow",
            password="workflow",
            port="5432",
            host="localhost",
        )
        cursor = conn.cursor()

        self.initReductionGroup(conn, cursor)

        reduction_data = self.getReductionData(instrument_scientist_client)

        instrument_scientist_client.post(self.URL_base + self.reduction_path, data=reduction_data, timeout=None)
        time.sleep(1)
        assert "this is a template" in self.getReductionScriptContents()

        # return reduce_ARCS.py back to starting state
        os.system(
            """docker exec -i data_workflow-autoreducer-1 bash -c \
            'cp /tmp/reduce_ARCS.py /SNS/ARCS/shared/autoreduce/reduce_ARCS.py'"""
        )
