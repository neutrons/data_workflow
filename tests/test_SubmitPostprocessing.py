import requests
import time
import psycopg2
import pytest

INSTRUMENT = "arcs"
RUN_NUMBER_GOOD = "201562"  # is in SNSdata.tar.gz
RUN_NUMBER_MISSING = "1234"  # does not exist
IPTS = "IPTS-27800"


class TestPostProcessingAdminView:
    def setup_class(cls):
        # connect to DB
        cls.conn = psycopg2.connect(
            database="workflow",
            user="workflow",
            password="workflow",
            port="5432",
            host="localhost",
        )

        cls.cursor = cls.conn.cursor()

        # get instrument_id
        cls.cursor.execute(f"SELECT id FROM report_instrument WHERE name = '{INSTRUMENT}';")
        cls.instrument_id = cls.cursor.fetchone()[0]

        # get ipts_id
        cls.cursor.execute(f"SELECT id FROM report_ipts WHERE expt_name = '{IPTS}';")
        cls.ipts_id = cls.cursor.fetchone()[0]

    def teardown_class(cls):
        # close DB connection
        cls.conn.close()

    def get_datarun_id(self, run_number):
        self.cursor.execute(
            f"SELECT id FROM report_datarun WHERE ipts_id_id = {self.ipts_id} "
            f"AND instrument_id_id = {self.instrument_id} "
            f"AND run_number = {run_number};"
        )

        fetch = self.cursor.fetchone()
        if fetch:
            return fetch[0]

    def get_session(self):
        URL = "http://localhost/users/login"
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username="workflow", password="workflow", csrfmiddlewaretoken=csrftoken)
        response = client.post(URL, data=login_data)
        assert response.status_code == 200
        return client

    def get_status_count(self, run_number):
        datarun_id = self.get_datarun_id(run_number)
        if datarun_id:
            self.cursor.execute(f"SELECT COUNT(*) FROM report_runstatus WHERE run_id_id = {datarun_id};")
            status_count = self.cursor.fetchone()[0]
        else:
            status_count = 0
        return status_count

    def send_request(self, task, run_number, requestType):
        client = self.get_session()
        data = dict(
            csrfmiddlewaretoken=client.cookies["csrftoken"],
            instrument=INSTRUMENT,
            experiment=IPTS,
            run_list=run_number,
            create_as_needed="on",
            task=task,  # not needed for requestType == find
            button_choice=requestType,
        )
        response = client.post("http://localhost/report/processing", data=data)
        assert response.status_code == 200
        time.sleep(1)
        return response.text

    def testPostProcessingSubmit(self):
        status_count = self.get_status_count(RUN_NUMBER_GOOD)

        # POSTPROCESS.DATA_READY, should add 6 new RunStatus
        self.send_request("POSTPROCESS.DATA_READY", RUN_NUMBER_GOOD, requestType="submit")

        new_status_count = self.get_status_count(RUN_NUMBER_GOOD)
        assert new_status_count - status_count == 10

        status_count = new_status_count

        # REDUCTION.NOT_NEEDED, should add 1 new RunStatus
        self.send_request("REDUCTION.NOT_NEEDED", RUN_NUMBER_GOOD, requestType="submit")

        new_status_count = self.get_status_count(RUN_NUMBER_GOOD)
        assert new_status_count - status_count == 1

        status_count = new_status_count

        # REDUCTION.REQUEST, should add 3 new RunStatus
        self.send_request("REDUCTION.REQUEST", RUN_NUMBER_GOOD, requestType="submit")

        new_status_count = self.get_status_count(RUN_NUMBER_GOOD)
        assert new_status_count - status_count == 7

        status_count = new_status_count

        # CATALOG.REQUEST, should add 4 new RunStatus
        self.send_request("CATALOG.REQUEST", RUN_NUMBER_GOOD, requestType="submit")

        new_status_count = self.get_status_count(RUN_NUMBER_GOOD)
        assert new_status_count - status_count == 4

    def testPostProcessingSubmitMissingRunfile(self):
        status_count = self.get_status_count(RUN_NUMBER_MISSING)

        # POSTPROCESS.DATA_READY, should add 6 new RunStatus
        self.send_request("POSTPROCESS.DATA_READY", RUN_NUMBER_MISSING, requestType="submit")

        new_status_count = self.get_status_count(RUN_NUMBER_MISSING)
        assert new_status_count - status_count == 6

    @pytest.mark.parametrize("run_number", [RUN_NUMBER_GOOD, RUN_NUMBER_MISSING])
    def testPostProcessingFind(self, run_number):
        """The find button reports all of the runs missing in a proposal"""
        status_count = self.get_status_count(run_number)

        html_page = self.send_request("", run_number, requestType="find")
        # html_page = self.send_request("POSTPROCESS.DATA_READY", run_number, requestType="find")

        new_status_count = self.get_status_count(run_number)
        assert new_status_count - status_count == 0

        assert "Missing runs:" in html_page
