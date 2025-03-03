"""This is to test that the reduction tasks go to the correct autoreducer node
depending on if it requires high memoery or not"""

import time

import tests.utils.db as db_utils


class TestAutoreducerQueues:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"
    conn = None
    instrument = "vulcan"
    IPTS = "IPTS-1234"
    run_number = 12345

    def set_reduction_request_queue(self, conn, queue_name):
        """create the task to send REDUCTION.REQUEST to the provided queue"""
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM report_instrument where name = %s;", (self.instrument,))
        inst_id = cursor.fetchone()[0]

        queue_id = db_utils.get_status_queue_id(conn, queue_name)
        success_queue_id = db_utils.get_status_queue_id(conn, "REDUCTION.COMPLETE")
        reduction_request_queue_id = db_utils.get_status_queue_id(conn, "REDUCTION.REQUEST")

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
            "INSERT INTO report_task_task_queue_ids (task_id, statusqueue_id) VALUES (%s, %s)",
            (task_id, queue_id),
        )
        cursor.execute(
            "INSERT INTO report_task_success_queue_ids (task_id, statusqueue_id) VALUES (%s, %s)",
            (task_id, success_queue_id),
        )
        conn.commit()

    def get_autoreducer_hostname(self, conn, run_id):
        """return the hostname that executed the task that is stored in the report information"""
        cursor = conn.cursor()
        queue_id = db_utils.get_status_queue_id(conn, "REDUCTION.STARTED")
        cursor.execute(
            "SELECT id FROM report_runstatus WHERE run_id_id = %s AND queue_id_id = %s",
            (run_id, queue_id),
        )
        runstatus_id = cursor.fetchone()[0]
        cursor.execute(
            "SELECT description FROM report_information WHERE run_status_id_id = %s",
            (runstatus_id,),
        )
        description = cursor.fetchone()[0]
        return description

    def test_normal_reduction_queue(self, db_connection, request_page):
        # switch to the REDUCTION.DATA_READY queue and check that the task goes to the correct node
        run_id = db_utils.add_instrument_data_run(db_connection, self.instrument, self.IPTS, self.run_number)
        db_utils.clear_previous_runstatus(db_connection, run_id)

        self.set_reduction_request_queue(db_connection, "REDUCTION.DATA_READY")

        # login and send reduction request
        response = request_page("/report/vulcan/12345/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/vulcan/12345/")

        # wait for database to get updated
        time.sleep(1.0)

        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.REQUEST")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.STARTED")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.DATA_READY")
        assert not db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.HIMEM.DATA_READY")

        assert self.get_autoreducer_hostname(db_connection, run_id) == "autoreducer"

    def test_himem_reduction_queue(self, db_connection, request_page):
        # switch to the REDUCTION.HIMEM.DATA_READY queue and check that the task goes to the correct node
        run_id = db_utils.add_instrument_data_run(db_connection, self.instrument, self.IPTS, self.run_number)
        db_utils.clear_previous_runstatus(db_connection, run_id)

        self.set_reduction_request_queue(db_connection, "REDUCTION.HIMEM.DATA_READY")
        # login and send reduction request
        response = request_page("/report/vulcan/12345/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/vulcan/12345/")

        # wait for database to get updated
        time.sleep(1.0)

        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.REQUEST")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.STARTED")
        assert not db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.DATA_READY")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.HIMEM.DATA_READY")

        assert self.get_autoreducer_hostname(db_connection, run_id) == "autoreducer.himem"
