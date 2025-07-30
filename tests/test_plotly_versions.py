import os

# Import the utility function for creating test data
import sys
import time

import psycopg2
import pytest
import requests

sys.path.append(os.path.join(os.path.dirname(__file__), "utils"))
from db import add_instrument_data_run

LIVEDATA_TEST_URL = "https://172.16.238.222"
WEBMON_TEST_URL = "http://localhost"


class TestPlotlyVersions:
    @classmethod
    def setup_class(cls):
        """Clean the database and create test data"""
        conn = psycopg2.connect(
            database=os.environ.get("DATABASE_NAME", "workflow"),
            user=os.environ.get("DATABASE_USER", "workflow"),
            password=os.environ.get("DATABASE_PASS", "workflow"),
            port=os.environ.get("DATABASE_PORT", 5432),
            host=os.environ.get("DATABASE_HOST", "localhost"),
        )
        cur = conn.cursor()

        # Clean up previous test data
        cur.execute("DELETE FROM plots_plotdata")
        cur.execute("DELETE FROM plots_datarun")
        cur.execute("DELETE FROM plots_instrument")
        conn.commit()

        # Create test data for ARCS run 214583
        add_instrument_data_run(conn, "arcs", "IPTS-27800", 214583)

        # Create test data for REF_L run 299096
        add_instrument_data_run(conn, "ref_l", "IPTS-33077", 299096)

        conn.close()

    def get_session(self):
        URL = WEBMON_TEST_URL + "/users/login"
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username="InstrumentScientist", password="InstrumentScientist", csrfmiddlewaretoken=csrftoken)
        response = client.post(URL, data=login_data)
        assert response.status_code == 200
        return client

    def send_request(self, task, run_number, requestType):
        client = self.get_session()
        data = dict(
            csrfmiddlewaretoken=client.cookies["csrftoken"],
            instrument="arcs",
            experiment="IPTS-27800",
            run_list=str(run_number),
            create_as_needed="on",
            task=task,
            button_choice=requestType,
        )
        url = WEBMON_TEST_URL + "/report/processing"
        response = client.post(url, data=data)
        return response

    @pytest.mark.skip(reason="Integration test requires full autoreduction pipeline to generate plot files")
    def test_publish_versions(self):
        """Test that plots are published with the correct plotlyjs-version attributes."""

        # Trigger reduction for ARCS (using autoreducer with Plotly v5)
        run_number_arcs = 214583
        response = self.send_request("reduction", run_number_arcs, "live_data")
        assert response.status_code == 200, f"ARCS reduction request failed: {response.status_code}"

        # Wait for processing
        time.sleep(30)

        # Check that ARCS plot has plotlyjs-version="5"
        plot_url = f"{LIVEDATA_TEST_URL}/files/arcs/IPTS-27800/shared/autoreduce/reduction_log/{run_number_arcs}/arcs_{run_number_arcs}_1d.html"  # noqa: E501
        plot_response = requests.get(plot_url, verify=False)
        assert plot_response.status_code == 200, f"Failed to fetch ARCS plot: {plot_response.status_code}"
        assert 'plotlyjs-version="5"' in plot_response.text, "ARCS plot should have plotlyjs-version='5'"

        # Trigger reduction for REF_L (using autoreducer_himem with Plotly v6)
        run_number_ref_l = 299096
        response = self.send_request("reduction", run_number_ref_l, "live_data")
        assert response.status_code == 200, f"REF_L reduction request failed: {response.status_code}"

        # Wait for processing
        time.sleep(30)

        # Check that REF_L plot has plotlyjs-version="6"
        plot_url = f"{LIVEDATA_TEST_URL}/files/ref_l/IPTS-33077/shared/autoreduce/reduction_log/{run_number_ref_l}/ref_l_{run_number_ref_l}_1d.html"  # noqa: E501
        plot_response = requests.get(plot_url, verify=False)
        assert plot_response.status_code == 200, f"Failed to fetch REF_L plot: {plot_response.status_code}"
        assert 'plotlyjs-version="6"' in plot_response.text, "REF_L plot should have plotlyjs-version='6'"

    def test_display_versions(self):
        """Test that the run report pages load successfully with proper authentication and data."""

        # Get authenticated session
        client = self.get_session()

        # Test ARCS run report page
        arcs_url = f"{WEBMON_TEST_URL}/report/arcs/214583/"
        response = client.get(arcs_url)
        assert response.status_code == 200, f"Failed to load ARCS run page: {response.status_code}"

        # Check that the page loads the detail template with correct content
        assert "Run 214583" in response.text, "Page should show run information"
        assert "ARCS" in response.text, "Page should show instrument name"
        assert "IPTS-27800" in response.text, "Page should show experiment information"

        # Verify this is the detail template (not an error or access denied page)
        assert "detail.html" not in response.text or "breadcrumbs" in response.text.lower(), (
            "Should load detail template"
        )

        # Test REF_L run report page
        ref_l_url = f"{WEBMON_TEST_URL}/report/ref_l/299096/"
        response = client.get(ref_l_url)
        assert response.status_code == 200, f"Failed to load REF_L run page: {response.status_code}"

        # Check that the page loads the detail template with correct content
        assert "Run 299096" in response.text, "Page should show run information"
        assert "REF_L" in response.text, "Page should show instrument name"
        assert "IPTS-33077" in response.text, "Page should show experiment information"

        # Verify this is the detail template (not an error or access denied page)
        assert "detail.html" not in response.text or "breadcrumbs" in response.text.lower(), (
            "Should load detail template"
        )
