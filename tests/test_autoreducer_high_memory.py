"""This is to test that the reduction tasks go to the correct autoreducer node
depending on if it requires high memoery or not"""
import psycopg2
import requests
import time
from dotenv import dotenv_values


class TestAutoreducerQueues:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"
    conn = None
    instrument = "vulcan"
    IPTS = "IPTS-1234"
    run_number = 12345

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

    def create_test_data(self):
        """create the instrument, ipts and datarun if they don't already exist

        returns the id for the created rundata"""
        conn = TestAutoreducerQueues.conn
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM report_instrument where name = %s;", (self.instrument,))
        inst_id = cursor.fetchone()

        if inst_id is None:
            cursor.execute("INSERT INTO report_instrument (name) VALUES (%s);", (self.instrument,))
            cursor.execute("SELECT id FROM report_instrument where name = %s;", (self.instrument,))
            inst_id = cursor.fetchone()
            conn.commit()

        cursor.execute("SELECT id FROM report_ipts WHERE expt_name = %s;", (self.IPTS,))
        ipts_id = cursor.fetchone()
        if ipts_id is None:
            cursor.execute(
                "INSERT INTO report_ipts (expt_name, created_on) VALUES (%s, %s);",
                ("IPTS-1234", "2020-05-20 13:02:52.281964;"),
            )
            cursor.execute("SELECT id FROM report_ipts WHERE expt_name = %s;", (self.IPTS,))
            ipts_id = cursor.fetchone()
            conn.commit()

        cursor.execute(
            "SELECT id FROM report_datarun WHERE run_number = %s AND ipts_id_id = %s AND instrument_id_id = %s;",
            (self.run_number, ipts_id[0], inst_id[0]),
        )
        run_id = cursor.fetchone()
        if run_id is None:
            cursor.execute(
                "INSERT INTO report_datarun (run_number, ipts_id_id, instrument_id_id, file, created_on) "
                "VALUES (%s, %s, %s, %s, %s);",
                (
                    self.run_number,
                    ipts_id[0],
                    inst_id[0],
                    "/SNS/VULCAN/IPTS-1234/nexus/VULCAN_12345.nxs.h5",
                    "2020-05-20 13:02:52.281964;",
                ),
            )
            cursor.execute(
                "SELECT id FROM report_datarun WHERE run_number = %s AND ipts_id_id = %s AND instrument_id_id = %s;",
                (self.run_number, ipts_id[0], inst_id[0]),
            )
            run_id = cursor.fetchone()
            conn.commit()

        return run_id

    def get_status_queue_id(self, cursor, queue_name):
        """return the if for the statusqueue for the provided name"""
        cursor.execute("SELECT id FROM report_statusqueue where name = %s;", (queue_name,))
        queue_id = cursor.fetchone()

        if queue_id is None:
            cursor.execute(
                "INSERT INTO report_statusqueue (name, is_workflow_input) VALUES (%s, %s);", (queue_name, False)
            )
            cursor.execute("SELECT id FROM report_statusqueue where name = %s;", (queue_name,))
            queue_id = cursor.fetchone()

        return queue_id[0]

    def set_reduction_request_queue(self, queue_name):
        """create the task to send REDUCTION.REQUEST to the provided queue"""
        conn = TestAutoreducerQueues.conn
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM report_instrument where name = %s;", (self.instrument,))
        inst_id = cursor.fetchone()[0]

        queue_id = self.get_status_queue_id(cursor, queue_name)
        success_queue_id = self.get_status_queue_id(cursor, "REDUCTION.COMPLETE")
        reduction_request_queue_id = self.get_status_queue_id(cursor, "REDUCTION.REQUEST")

        cursor.execute(
            "SELECT id FROM report_task where instrument_id_id = %s AND input_queue_id_id = %s;",
            (inst_id, reduction_request_queue_id),
        )
        task_id = cursor.fetchone()

        if task_id is None:
            cursor.execute(
                "INSERT INTO report_task (instrument_id_id, input_queue_id_id) VALUES (%s, %s)",
                (inst_id, reduction_request_queue_id),
            )
            cursor.execute(
                "SELECT id FROM report_task where instrument_id_id = %s AND input_queue_id_id = %s;",
                (inst_id, reduction_request_queue_id),
            )
            task_id = cursor.fetchone()
            conn.commit()

        task_id = task_id[0]

        cursor.execute("DELETE FROM report_task_task_queue_ids WHERE task_id = %s", (task_id,))
        cursor.execute("DELETE FROM report_task_success_queue_ids WHERE task_id = %s", (task_id,))

        cursor.execute(
            "INSERT INTO report_task_task_queue_ids (task_id, statusqueue_id) VALUES (%s, %s)", (task_id, queue_id)
        )
        cursor.execute(
            "INSERT INTO report_task_success_queue_ids (task_id, statusqueue_id) VALUES (%s, %s)",
            (task_id, success_queue_id),
        )
        conn.commit()

    def clear_previous_runstatus(self, run_id):
        """remove all previous run statuses for the given run_id"""
        conn = TestAutoreducerQueues.conn
        cursor = conn.cursor()
        # delete all information entries for runstatus
        cursor.execute(
            "DELETE FROM report_information WHERE run_status_id_id IN (SELECT id FROM report_runstatus "
            "WHERE run_id_id = %s);",
            run_id,
        )
        cursor.execute("DELETE FROM report_runstatus WHERE run_id_id = %s;", run_id)
        conn.commit()

    def get_autoreducer_hostname(self, run_id):
        """return the hostname that executed the task that is stored in the report information"""
        conn = TestAutoreducerQueues.conn
        cursor = conn.cursor()
        queue_id = self.get_status_queue_id(cursor, "REDUCTION.STARTED")
        cursor.execute("SELECT id FROM report_runstatus WHERE run_id_id = %s AND queue_id_id = %s", (run_id, queue_id))
        runstatus_id = cursor.fetchone()[0]
        cursor.execute("SELECT description FROM report_information WHERE run_status_id_id = %s", (runstatus_id,))
        description = cursor.fetchone()[0]
        return description

    def check_run_status_exist(self, run_id, queue_name):
        """return if the run status was created for the given run_id and queue_name"""
        conn = TestAutoreducerQueues.conn
        cursor = conn.cursor()
        queue_id = self.get_status_queue_id(cursor, queue_name)
        cursor.execute("SELECT * FROM report_runstatus WHERE run_id_id = %s AND queue_id_id = %s", (run_id, queue_id))
        return cursor.fetchone() is not None

    def test_normal_reduction_queue(self):
        # switch to the REDUCTION.DATA_READY queue and check that the task goes to the correct node
        run_id = self.create_test_data()
        self.clear_previous_runstatus(run_id)

        self.set_reduction_request_queue("REDUCTION.DATA_READY")

        # login and send reduction request
        response = self.login("/report/vulcan/12345/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/vulcan/12345/")

        # wait for database to get updated
        time.sleep(1.0)

        assert self.check_run_status_exist(run_id, "REDUCTION.REQUEST")
        assert self.check_run_status_exist(run_id, "REDUCTION.STARTED")
        assert self.check_run_status_exist(run_id, "REDUCTION.DATA_READY")
        assert not self.check_run_status_exist(run_id, "REDUCTION.HIMEM.DATA_READY")

        assert self.get_autoreducer_hostname(run_id) == "autoreducer"

    def test_himem_reduction_queue(self):
        # switch to the REDUCTION.HIMEM.DATA_READY queue and check that the task goes to the correct node
        run_id = self.create_test_data()
        self.clear_previous_runstatus(run_id)

        self.set_reduction_request_queue("REDUCTION.HIMEM.DATA_READY")
        # login and send reduction request
        response = self.login("/report/vulcan/12345/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/vulcan/12345/")

        # wait for database to get updated
        time.sleep(1.0)

        assert self.check_run_status_exist(run_id, "REDUCTION.REQUEST")
        assert self.check_run_status_exist(run_id, "REDUCTION.STARTED")
        assert not self.check_run_status_exist(run_id, "REDUCTION.DATA_READY")
        assert self.check_run_status_exist(run_id, "REDUCTION.HIMEM.DATA_READY")

        assert self.get_autoreducer_hostname(run_id) == "autoreducer.himem"
