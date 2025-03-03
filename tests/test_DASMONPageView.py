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
        expected_number_of_entries = 57
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
        # -- Workflow idagnostics
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
        # -- Reduction queue lengths
        assert table_content[31] == "REDUCTION.DATA_READY"
        assert table_content[33] == "0"
        assert table_content[34] == "REDUCTION_CATALOG.DATA_READY"
        assert table_content[36] == "0"
        assert table_content[37] == "CATALOG.ONCAT.DATA_READY"
        assert table_content[39] == "0"


if __name__ == "__main__":
    pytest.main()
