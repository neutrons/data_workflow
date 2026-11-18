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

        # check rows by label, not a cell count: the row count depends on what already ran
        # (each autoreducer gets a "Last msg" row after its first job)
        rows = table_rows(dasmon_diagnostics.text)

        # -- DASMON, PVSD and Workflow, in page order
        assert [row[1] for row in rows if row[0] == "Last status:"] == ["0", "-1", "0"]
        last_updates = [row for row in rows if row[0] == "Last status update:"]
        assert len(last_updates) == 3
        assert all(len(row) == 2 and row[1] for row in last_updates)
        assert any(row[0] == "Last PV update:" and len(row) == 2 and row[1] for row in rows)
        assert any(row[0] == "Last AMQ update:" and len(row) == 2 and row[1] for row in rows)
        assert any(row[0].startswith("Dasmon listener PID") and len(row) == 2 and row[1] for row in rows)

        # -- Cataloging & Reduction
        assert any(len(row) == 3 and row[0].startswith("autoreducer") and row[2].startswith("PID:") for row in rows)

        # -- Reduction queue lengths: every queue reported so far (no table until the first sample)
        queue_table = "//table[.//th[normalize-space()='Queue']]//tr[td]"
        for row in table_rows(dasmon_diagnostics.text, queue_table):
            assert len(row) == 3 and row[0] and row[1], row
            assert row[2].isdigit(), row


def table_rows(html, xpath="//tr[td]"):
    """Table rows as lists of cell texts, one per <td>, with empty cells kept as ""."""
    tree = etree.parse(StringIO(html), etree.HTMLParser())
    return [["".join(td.itertext()).strip() for td in tr.xpath("./td")] for tr in tree.xpath(xpath)]


if __name__ == "__main__":
    pytest.main()
