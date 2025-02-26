import time
import os
import hashlib

import psycopg2
import requests

LIVEDATA_TEST_URL = "https://172.16.238.222"
WEBMON_TEST_URL = "http://localhost"


class TestLiveDataServer:
    instrument = "arcs"
    IPTS = "IPTS-27800"
    run_number = 214583

    @classmethod
    def setup_class(cls):
        """Clean the database before running tests"""
        conn = psycopg2.connect(
            database=os.environ.get("DATABASE_NAME", "workflow"),
            user=os.environ.get("DATABASE_USER", "workflow"),
            password=os.environ.get("DATABASE_PASS", "workflow"),
            port=os.environ.get("DATABASE_PORT", 5432),
            host="localhost",
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM plots_plotdata")
        cur.execute("DELETE FROM plots_datarun")
        cur.execute("DELETE FROM plots_instrument")
        conn.commit()
        conn.close()

    def get_session(self):
        URL = WEBMON_TEST_URL + "/users/login"
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username="workflow", password="workflow", csrfmiddlewaretoken=csrftoken)
        response = client.post(URL, data=login_data)
        assert response.status_code == 200
        return client

    def send_request(self, task, run_number, requestType):
        client = self.get_session()
        data = dict(
            csrfmiddlewaretoken=client.cookies["csrftoken"],
            instrument=self.instrument,
            experiment=self.IPTS,
            run_list=self.run_number,
            create_as_needed="on",
            task=task,
            button_choice=requestType,
        )
        response = client.post(WEBMON_TEST_URL + "/report/processing", data=data)
        assert response.status_code == 200
        time.sleep(1)
        return response.text

    def test_reduction_request_livedata(self):
        ssl_crt_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../nginx/nginx.crt")

        key = generate_key(self.instrument, self.run_number)
        # first check that the there isn't an existing plot, should 404
        response = requests.get(
            f"{LIVEDATA_TEST_URL}/plots/{self.instrument}/{self.run_number}/update/html/?key={key}",
            verify=ssl_crt_filename,
        )
        assert response.status_code == 404

        # send data ready request, which should trigger autoreduction and therefore publish a plot to livedata
        self.send_request("POSTPROCESS.DATA_READY", 123456, requestType="submit")

        # the data should now be on livedata
        response = requests.get(
            f"{LIVEDATA_TEST_URL}/plots/{self.instrument}/{self.run_number}/update/html/?key={key}",
            verify=ssl_crt_filename,
        )
        assert response.status_code == 200
        assert "Example Plot Data" in response.text
        assert "Filename: /SNS/ARCS/IPTS-27800/nexus/ARCS_214583.nxs.h5" in response.text
        assert "Hostname: autoreducer" in response.text

        # now verify that the run report page is templated correctly
        client = self.get_session()
        page = client.get(f"{WEBMON_TEST_URL}/report/{self.instrument}/{self.run_number}/")
        assert f"https://172.16.238.222:443/plots/arcs/214583/update/html/?key={key}" in page.text


def generate_key(instrument, run_id):
    """
    Generate a secret key for a run on a given instrument
    Used to simulate clients sending GET-requests using a secret key
    @param instrument: instrument name
    @param run_id: run number
    """
    secret_key = os.environ.get("LIVE_PLOT_SECRET_KEY")
    if secret_key is None or len(secret_key) == 0:
        return None

    return hashlib.sha1(f"{instrument.upper()}{secret_key}{run_id}".encode("utf-8")).hexdigest()
