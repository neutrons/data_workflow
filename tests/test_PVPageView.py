import requests
import re
from datetime import datetime


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def check_PV(text, PV):
    # BL18:SE:SampleTemp
    assert f"new_monitor('{PV}', '1');" in text

    value = re.findall(f'<td><span id="{PV}">.*</span></td>', text)
    assert len(value) == 1
    value = re.findall(r"\d+\.\d+", value[0])[0]
    assert is_float(value)

    # just check that a new PV arrived in the last two minutes
    time = re.findall(f'<td><span id="{PV}_timestamp">.*</span></td>', text)
    assert len(time) == 1
    time = datetime.strptime(
        time[0]
        .replace(f'<td><span id="{PV}_timestamp">', "")
        .replace("</span></td>", "")
        .replace("a.m.", "AM")
        .replace("p.m.", "PM"),
        "%B %d, %Y, %I:%M %p",
    )
    time_delta = datetime.now() - time
    assert time_delta.total_seconds() < 120


class TestPVPageView:
    def login(self, next, username, password):
        URL = "http://localhost/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        return client.post(URL + next, data=login_data, timeout=None)

    def test_arcs_PV_page(self):
        response = self.login("/pvmon/arcs/", "postgres", "postgres")
        assert response.status_code == 200

        check_PV(response.text, "BL18:SE:SampleTemp")
        check_PV(response.text, "chopper3_TDC")
        check_PV(response.text, "LKS1A")
        check_PV(response.text, "LKS1B")
        check_PV(response.text, "LKS1C")
