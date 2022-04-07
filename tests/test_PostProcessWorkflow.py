import psycopg2
import requests


class TestPostProcessingWorkflow:
    user = "postgres"
    pwd = "postgres"

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

    def test_catalog(self):
        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )

        cursor = conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        queue_id = self.get_queue_id(cursor, "CATALOG.REQUEST")
        started_id = self.get_queue_id(cursor, "CATALOG.STARTED")
        ready_id = self.get_queue_id(cursor, "CATALOG.DATA_READY")
        complete_id = self.get_queue_id(cursor, "CATALOG.COMPLETE")

        # get current catalog status counts
        queues = [queue_id, started_id, ready_id, complete_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send catalog request
        response = self.login("/report/arcs/214583/catalog/", self.user, self.pwd)
        assert response.status_code == 200

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

        conn.close()

    def test_reduction(self):
        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )

        cursor = conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        queue_id = self.get_queue_id(cursor, "REDUCTION.REQUEST")
        ready_id = self.get_queue_id(cursor, "REDUCTION.DATA_READY")

        # get current reduction status counts
        queues = [queue_id, ready_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send reduction request
        response = self.login("/report/arcs/214583/reduce/", self.user, self.pwd)
        assert response.status_code == 200

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

        conn.close()

    def test_postprocess(self):
        conn = psycopg2.connect(
            database="workflow",
            user="postgres",
            password="postgres",
            port="5432",
            host="localhost",
        )

        cursor = conn.cursor()

        datarun_id = self.get_datarun_id(cursor, "arcs", "IPTS-27800", "214583")

        ready_id = self.get_queue_id(cursor, "POSTPROCESS.DATA_READY")

        # get current reduction status counts
        queues = [ready_id]
        counts_before = self.get_message_counts(cursor, datarun_id, queues)

        # login and send all-post process request
        response = self.login("/report/arcs/214583/postprocess/", self.user, self.pwd)
        assert response.status_code == 200

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

        conn.close()
