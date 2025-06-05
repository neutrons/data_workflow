"""Test the status acquiring appears when a SMS message is received and before the data is ready"""

import json
import time

import tests.utils.db as db_utils


class TestSMSQueues:
    instrument = "arcs"
    IPTS = "IPTS-11111"
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"

    def create_and_send_msg(self, conn, run_number):
        conn.send(
            f"/topic/SNS.{self.instrument.upper()}.APP.SMS",
            json.dumps(
                {
                    "instrument": self.instrument,
                    "facility": "SNS",
                    "ipts": self.IPTS,
                    "run_number": run_number,
                    "data_file": "",
                    "reason": "SMS run started",
                    "msg_type": "0",
                }
            ),
        )

    def clear_run(self, conn, run_number):
        # remove everything for this run
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM report_instrument where name = %s;", (self.instrument,))
        inst_id = cursor.fetchone()
        if inst_id is None:
            return

        cursor.execute(
            "SELECT id FROM report_datarun WHERE instrument_id_id = %s AND run_number = %s;", (inst_id, run_number)
        )
        run_id = cursor.fetchone()
        if run_id is None:
            return

        db_utils.clear_previous_runstatus(conn, run_id)
        cursor.execute("DELETE FROM report_workflowsummary WHERE run_id_id = %s;", run_id)
        cursor.execute("DELETE FROM report_instrumentstatus WHERE last_run_id_id = %s;", run_id)
        cursor.execute("DELETE FROM report_datarun WHERE id = %s;", (run_id))
        conn.commit()
        cursor.close()

    def test_acquiring(self, amq_connection, db_connection, request_page):
        # remove data run so the tests always starts fresh
        self.clear_run(db_connection, 100)
        self.clear_run(db_connection, 101)
        # send SMS message for 2 runs
        self.create_and_send_msg(amq_connection, 100)
        self.create_and_send_msg(amq_connection, 101)

        # wait a second while things run
        time.sleep(1)

        # check IPTS page /report/arcs/experiment/IPTS-11111/update/ for acquiring
        response = request_page("/report/arcs/experiment/IPTS-11111/update/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.text.count("acquiring") == 2

        # now send data_ready for run 100 only and check that it is no longer acquiring
        self.create_and_send_msg(amq_connection, 100)

        amq_connection.send(
            "/queue/POSTPROCESS.DATA_READY",
            json.dumps(
                {
                    "instrument": self.instrument,
                    "facility": "SNS",
                    "ipts": self.IPTS,
                    "run_number": 100,
                    "data_file": "",
                }
            ),
        )
        time.sleep(1)

        # check IPTS page /report/arcs/experiment/IPTS-11111/update/ for acquiring
        response = request_page("/report/arcs/experiment/IPTS-11111/update/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.text.count("acquiring") == 1  # 101 is still acquiring but not 100
