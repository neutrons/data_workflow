import time

import psycopg2
import requests
from django.conf import settings
from dotenv import dotenv_values


class TestPostProcessingWorkflow:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"
    conn = None

    def setup_class(cls):
        config = {**dotenv_values(".env"), **dotenv_values(".env.ci")}
        assert config
        cls.conn = psycopg2.connect(
            database=config["DATABASE_NAME"],
            user=config["DATABASE_USER"],
            password=config["DATABASE_PASS"],
            port=config["DATABASE_PORT"],
            host="localhost",
        )
        time.sleep(1)

    def teardown_class(cls):
        cls.conn.close()

    def login(self, next, username, password):
        # taken from test_RunPageView.py - consolidate as helper somewhere?
        URL = "http://localhost/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        return client.post(URL + next, data=login_data, timeout=None)

    def get_datarun_id(self, cursor, instr_name, ipts, run):
        file = f"'/SNS/{instr_name.upper()}/{ipts}/nexus/{instr_name.upper()}_{run}.nxs.h5'"
        cursor.execute(f"SELECT id FROM report_datarun WHERE run_number = {run} AND file = {file};")
        datarun_id = cursor.fetchone()[0]

        return datarun_id

    def get_queue_id(self, cursor, queue_name):
        cursor.execute(f"SELECT id FROM report_statusqueue WHERE name = '{queue_name}';")
        return cursor.fetchone()[0]

    def get_message_counts(self, cursor, datarun_id, queue_ids):
        """
        Test helper to get message counts for the given datarun for each queue id
        Returns dict of counts indexed by queue id
        """
        counts = dict()
        for queue in queue_ids:
            cursor.execute(
                f"SELECT COUNT(*) FROM report_runstatus WHERE run_id_id = {datarun_id} AND queue_id_id = {queue};"
            )
            counts[queue] = cursor.fetchone()[0]
        return counts

    def get_status_errors(self, cursor, datarun_id):
        cursor.execute(f"SELECT * FROM report_runstatus WHERE run_id_id = {datarun_id};")
        errors = []
        status_messages = cursor.fetchall()
        for message in status_messages:
            # check if this message appears in the error table
            cursor.execute(f"SELECT * FROM report_error WHERE run_status_id_id = {message[0]};")
            result = cursor.fetchall()
            if len(result) > 0:
                errors.append(result)
        return errors

    def test_catalog(self):
        cursor = self.__class__.conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        queue_id = self.get_queue_id(cursor, "CATALOG.REQUEST")
        started_id = self.get_queue_id(cursor, "CATALOG.ONCAT.STARTED")
        ready_id = self.get_queue_id(cursor, "CATALOG.ONCAT.DATA_READY")
        complete_id = self.get_queue_id(cursor, "CATALOG.ONCAT.COMPLETE")
        error_id = self.get_queue_id(cursor, "CATALOG.ONCAT.ERROR")

        # get current catalog status counts
        queues = [queue_id, started_id, ready_id, complete_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send catalog request
        response = self.login("/report/arcs/214583/catalog/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/arcs/214583/")

        # wait for database to get updated
        time.sleep(1.0)

        # make sure no catalog error appeared
        assert self.get_message_counts(cursor, datarun_id, [error_id])[error_id] == 0
        assert len(self.get_status_errors(cursor, datarun_id)) == 0

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        assert counts_after[queue_id] - counts_before[queue_id] == 1
        assert counts_after[started_id] - counts_before[started_id] == 1
        assert counts_after[ready_id] - counts_before[ready_id] == 1
        assert counts_after[complete_id] - counts_before[complete_id] == 1

    def test_reduction(self):
        cursor = self.__class__.conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        queue_id = self.get_queue_id(cursor, "REDUCTION.REQUEST")
        ready_id = self.get_queue_id(cursor, "REDUCTION.DATA_READY")

        # get current reduction status counts
        queues = [queue_id, ready_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send reduction request
        response = self.login("/report/arcs/214583/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/arcs/214583/")

        # wait for database to get updated
        time.sleep(1.0)

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

    def test_postprocess(self):
        cursor = self.__class__.conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        ready_id = self.get_queue_id(cursor, "POSTPROCESS.DATA_READY")

        # get current reduction status counts
        queues = [ready_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send all-post process request
        response = self.login("/report/arcs/214583/postprocess/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/arcs/214583/")

        # wait for database to get updated
        time.sleep(1.0)

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

    def test_guest_access(self):
        # sending a catalog request as a guest user should be denied
        cursor = self.__class__.conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")
        queues = [self.get_queue_id(cursor, "CATALOG.REQUEST")]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        response = self.login(
            "/report/arcs/214583/catalog/", settings.GENERAL_USER_USERNAME, settings.GENERAL_USER_PASSWORD
        )
        assert response.status_code == 200
        assert response.url.endswith("/report/arcs/214583/")
        assert "You do not have access" in response.text

        # wait for database to get updated
        time.sleep(0.5)

        # no new database entry should appear since request was denied
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        assert counts_before == counts_after
