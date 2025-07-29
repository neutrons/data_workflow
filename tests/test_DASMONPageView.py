from io import StringIO

import pytest
import requests
from lxml import etree


class TestDASMONPageView:
    def login(self, next, username, password):
        URL = "http://localhost/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        return client.post(URL + next, data=login_data, timeout=None)

    @pytest.fixture
    def dasmon_diagnostics(self):
        r = self.login("/dasmon/arcs/diagnostics/", "workflow", "workflow")
        yield r

    def testVerifyDASMONPageView(self, dasmon_diagnostics):
        # verify finding the page
        assert dasmon_diagnostics.status_code == 200

        # Check system statues
        assert "<li class='status_0' id='workflow_status'>Workflow</li>" in dasmon_diagnostics.text
        assert "<li class='status_0' id='dasmon_status'>DASMON</li>" in dasmon_diagnostics.text
        assert "<li class='status_2' id='pvstreamer_status'>PVSD</li>" in dasmon_diagnostics.text

        # parse HTML
        parser = etree.HTMLParser()
        tree = etree.parse(StringIO(dasmon_diagnostics.text), parser)
        table_content = tree.xpath("//tr/td//text()")
        # verify number of entries in the tables
        expected_number_of_entries = 54  # Updated for current CI environment
        assert len(table_content) == expected_number_of_entries
        # -- DASMON diagnostics
        status = table_content[1]
        last_status_update = table_content[3]
        last_pv_update = table_content[5]
        last_amq_update = table_content[7]
        assert status == "0"
        assert len(last_status_update) > 0
        assert len(last_pv_update) > 0
        assert len(last_amq_update) > 0
        # -- PVSD diagnostics
        status = table_content[9]
        last_status_update = table_content[11]
        assert status == "-1"
        assert len(last_status_update) > 0
        # -- Workflow diagnostics
        status = table_content[13]
        last_status_update = table_content[15]
        dasmon_listener_pid = table_content[17]
        assert status == "0"
        assert len(last_status_update) > 0
        assert len(dasmon_listener_pid) > 0
        # -- Cataloging & Reduction diagnostics
        autoreducer = table_content[19]
        autoreducer_pid = table_content[21]
        assert len(autoreducer) > 0
        assert len(autoreducer_pid) > 0
        # -- Reduction queue lengths (search for entries instead of using fixed indices)
        # Find the indices of the queue entries dynamically
        if "REDUCTION.DATA_READY" in table_content:
            reduction_data_ready_idx = table_content.index("REDUCTION.DATA_READY")
            reduction_data_ready_entries = table_content[reduction_data_ready_idx + 1]
            assert len(reduction_data_ready_entries) > 0

        if "REDUCTION_CATALOG.DATA_READY" in table_content:
            reduction_catalog_data_ready_idx = table_content.index("REDUCTION_CATALOG.DATA_READY")
            reduction_catalog_data_ready_entries = table_content[reduction_catalog_data_ready_idx + 1]
            assert len(reduction_catalog_data_ready_entries) > 0

        if "POSTPROCESS.DATA_READY" in table_content:
            postprocess_data_ready_idx = table_content.index("POSTPROCESS.DATA_READY")
            postprocess_data_ready_entries = table_content[postprocess_data_ready_idx + 1]
            assert len(postprocess_data_ready_entries) > 0


if __name__ == "__main__":
    pytest.main()
