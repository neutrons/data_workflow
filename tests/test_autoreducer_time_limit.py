"""
Test of the autoreducer memory management that sets a max limit
on the memory used by reduction scripts.
"""

import time

import tests.utils.db as db_utils


class TestAutoreducerTimeLimit:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"
    instrument = "nom"
    IPTS = "IPTS-1001"
    run_number = 10002

    def test_reduction_script_exceeds_time_limit(self, db_connection, request_page):
        """test that the reduction is terminated and an error is logged"""
        run_id = db_utils.add_instrument_data_run(db_connection, self.instrument, self.IPTS, self.run_number)
        db_utils.clear_previous_runstatus(db_connection, run_id)

        # login and send reduction request
        response = request_page("/report/nom/10002/reduce/", self.user, self.pwd)
        assert response.status_code == 200
        assert response.url.endswith("/report/nom/10002/")

        # wait for reduction job to be terminated and database to be updated
        # note: the post-processing task time limit is set to 6 seconds, since if it is too short,
        # the memory limit test will hit the time limit before it hits the memory limit
        time.sleep(7.0)

        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.REQUEST")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.STARTED")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.DATA_READY")
        assert db_utils.check_run_status_exist(db_connection, run_id, "REDUCTION.ERROR")

        assert db_utils.check_error_msg_contains(db_connection, run_id, "Time limit exceeded")
