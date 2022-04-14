import psycopg2
import requests
from django.conf import settings


class TestPostProcessingWorkflow:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"
    conn = None

    def setup_class(cls):
        assert settings.configured
        cls.conn = psycopg2.connect(
            database=settings.DATABASES["default"]["NAME"],
            user=settings.DATABASES["default"]["USER"],
            password=settings.DATABASES["default"]["PASSWORD"],
            port=settings.DATABASES["default"]["PORT"],
            host=settings.DATABASES["default"]["HOST"],
        )

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

    def test_catalog(self):
        cursor = self.__class__.conn.cursor()

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
        assert response.url.endswith("/report/arcs/214583/")

        # wait for database to get updated
        time.sleep(3.0)

        # A status entry should appear for each kind of queue
        counts_after = self.get_message_counts(cursor, datarun_id, queues)
        for queue in queues:
            assert counts_after[queue] - counts_before[queue] == 1

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
