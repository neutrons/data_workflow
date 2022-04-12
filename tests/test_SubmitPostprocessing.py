import requests
import time
import os
import psycopg2


class TestPostProcessingAdminView:
    instrument = "arcs"
    run_number = "83809710"
    ipts = "IPTS-27800"

    def setup_class(cls):
        # Make sure data file exists in autoreducer container
        os.system("docker exec data_workflow_autoreducer_1 "
                  f"touch /SNS/ARCS/{cls.ipts}/nexus/ARCS_{cls.run_number}.nxs.h5")

        # connect to DB
        cls.conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )

        cls.cursor = cls.conn.cursor()

        # get instrument_id
        cls.cursor.execute(f"SELECT id FROM report_instrument WHERE name = '{cls.instrument}';")
        cls.instrument_id = cls.cursor.fetchone()[0]

        # get ipts_id
        cls.cursor.execute(f"SELECT id FROM report_ipts WHERE expt_name = '{cls.ipts}';")
        cls.ipts_id = cls.cursor.fetchone()[0]

    def teardown_class(cls):
        # close DB connection
        cls.conn.close()

    def get_datarun_id(self):
        self.cursor.execute(
            f"SELECT id FROM report_datarun WHERE ipts_id_id = {self.ipts_id} "
            f"AND instrument_id_id = {self.instrument_id} "
            f"AND run_number = {self.run_number};"
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

        login_data = dict(username="postgres", password="postgres", csrfmiddlewaretoken=csrftoken)
        response = client.post(URL, data=login_data)
        assert response.status_code == 200
        return client

    def get_status_count(self):
        datarun_id = self.get_datarun_id()
        if datarun_id:
            self.cursor.execute(f"SELECT COUNT(*) FROM report_runstatus WHERE run_id_id = {datarun_id};")
            status_count = self.cursor.fetchone()[0]
        else:
            status_count = 0
        return status_count

    def send_request(self, task):
        client = self.get_session()
        data = dict(csrfmiddlewaretoken=client.cookies["csrftoken"],
                    instrument=self.instrument,
                    experiment=self.ipts,
                    run_list=self.run_number,
                    create_as_needed="on",
                    task=task,
                    button_choice="submit")
        response = client.post("http://localhost/report/processing", data=data)
        assert response.status_code == 200
        time.sleep(1)

    def testPostProcessingAdmin(self):
        status_count = self.get_status_count()

        # POSTPROCESS.DATA_READY, should add 6 new RunStatus
        self.send_request("POSTPROCESS.DATA_READY")

        new_status_count = self.get_status_count()
        assert new_status_count - status_count == 10

        status_count = new_status_count

        # REDUCTION.NOT_NEEDED, should add 1 new RunStatus
        self.send_request("REDUCTION.NOT_NEEDED")

        new_status_count = self.get_status_count()
        assert new_status_count - status_count == 1

        status_count = new_status_count

        # REDUCTION.REQUEST, should add 3 new RunStatus
        self.send_request("REDUCTION.REQUEST")

        new_status_count = self.get_status_count()
        assert new_status_count - status_count == 7

        status_count = new_status_count

        # CATALOG.REQUEST, should add 4 new RunStatus
        self.send_request("CATALOG.REQUEST")

        new_status_count = self.get_status_count()
        assert new_status_count - status_count == 4
