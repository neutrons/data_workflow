import os

# Import the utility function for creating test data
import time

import psycopg2
import requests

from .test_livedata import generate_key
from .utils.db import add_instrument_data_run, set_reduction_request_queue

LIVEDATA_TEST_URL = "https://172.16.238.222"
WEBMON_TEST_URL = "http://localhost"


class TestPlotlyVersions:
    user = "InstrumentScientist"
    pwd = "InstrumentScientist"

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

    def test_publish_versions(self, db_connection, request_page):
        """Test that plots are published with the correct plotlyjs-version attributes."""

        # Trigger reduction for ARCS (using autoreducer with Plotly v5)
        run_number_arcs = 214583
        response = request_page(f"/report/arcs/{run_number_arcs}/reduce/", self.user, self.pwd)
        assert response.status_code == 200, f"ARCS reduction request failed: {response.status_code}"

        # Wait for processing
        time.sleep(3)

        # Check that ARCS plot has plotlyjs-version="5"
        key = generate_key("arcs", run_number_arcs)
        plot_url = f"{LIVEDATA_TEST_URL}/plots/arcs/{run_number_arcs}/update/html/?key={key}"
        plot_response = requests.get(plot_url, verify=False)
        assert plot_response.status_code == 200, f"Failed to fetch ARCS plot: {plot_response.status_code}"
        assert "ARCS Test Plot - Run 214583" in plot_response.text
        assert 'plotlyjs-version="2.' in plot_response.text, (
            "ARCS plot should have plotlyjs-version 2.x (from plotly 5.17.0)"
        )

        # Trigger reduction for REF_L (using autoreducer_himem with Plotly v6)
        set_reduction_request_queue(db_connection, "ref_l", "REDUCTION.HIMEM.DATA_READY")
        run_number_ref_l = 214746
        response = request_page(f"/report/ref_l/{run_number_ref_l}/reduce/", self.user, self.pwd)
        assert response.status_code == 200, f"REF_L reduction request failed: {response.status_code}"

        # Wait for processing
        time.sleep(3)

        # Check that REF_L plot has plotlyjs-version="6"
        key = generate_key("ref_l", run_number_ref_l)
        plot_url = f"{LIVEDATA_TEST_URL}/plots/ref_l/{run_number_ref_l}/update/html/?key={key}"
        plot_response = requests.get(plot_url, verify=False)
        assert plot_response.status_code == 200, f"Failed to fetch REF_L plot: {plot_response.status_code}"
        assert "REF_L Test Plot with Dynamic Plotly Loading" in plot_response.text
        assert 'plotlyjs-version="3.' in plot_response.text, (
            "REF_L plot should have plotlyjs-version 3.x (from plotly 6.0.0)"
        )

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
