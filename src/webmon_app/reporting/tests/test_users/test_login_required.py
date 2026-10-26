from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from workflow.database.report.models import IPTS, DataRun

from reporting.report.models import Instrument

# An anonymous request that looks as local as possible: the test client's default
# REMOTE_ADDR of 127.0.0.1, a spoofed X-Real-IP header, and an ORNL reverse-DNS name.
LOCAL_LOOKING = {"HTTP_X_REAL_IP": "127.0.0.1"}


@mock.patch("socket.gethostbyaddr", return_value=("bl4b-ws1.sns.gov", [], ["127.0.0.1"]))
class TestLoginRequired(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(username="user1", password="pw")
        instrument = Instrument.objects.create(name="ref_l")
        ipts = IPTS.objects.create(expt_name="ipts-1234")
        DataRun.objects.create(run_number=7, ipts_id=ipts, instrument_id=instrument, file="/tmp/REF_L_7.nxs.h5")

    def test_ajax_update_needs_login(self, mock_gethostbyaddr):
        for url in (
            reverse("pvmon:get_update", args=["ref_l"]),
            reverse("report:get_instrument_update", args=["ref_l"]),
        ):
            response = self.client.get(url, **LOCAL_LOOKING)
            self.assertEqual(response.status_code, 401, url)

    def test_pages_redirect_to_login(self, mock_gethostbyaddr):
        for url in (reverse("dasmon:dashboard_complete"), reverse("report:summary")):
            response = self.client.get(url, **LOCAL_LOOKING)
            self.assertEqual(response.status_code, 302, url)
            self.assertEqual(response.url, f"/users/login?next={url}")

    def test_landing_page_is_public(self, mock_gethostbyaddr):
        for url in (
            reverse("dasmon:dashboard"),
            reverse("dasmon:dashboard_update"),
            reverse("dasmon:summary_update"),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)

    def test_dashboard_rates_need_login(self, mock_gethostbyaddr):
        # ?plots is only used by the full dashboard, which requires a login
        url = reverse("dasmon:dashboard_update") + "?plots"
        self.assertEqual(self.client.get(url, **LOCAL_LOOKING).status_code, 401)

        self.assertTrue(self.client.login(username="user1", password="pw"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("instrument_rates", response.json())

    def test_unknown_instrument_update_is_404(self, mock_gethostbyaddr):
        url = reverse("dasmon:get_update", args=["no_such_instrument"])
        self.assertEqual(self.client.get(url).status_code, 404)

        self.assertTrue(self.client.login(username="user1", password="pw"))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_instrument_update_only_shows_status_when_logged_out(self, mock_gethostbyaddr):
        url = reverse("dasmon:get_update", args=["ref_l"])

        response = self.client.get(url, **LOCAL_LOOKING)
        self.assertEqual(response.status_code, 200)
        info = response.json()
        self.assertEqual(sorted(info), ["das_status", "last_expt", "last_run"])
        # what AdaraMonitor reads
        for service in ("dasmon", "pvstreamer", "workflow", "catalog", "reduction"):
            self.assertIn(service, info["das_status"])
        self.assertEqual(info["last_run"], 7)
        self.assertEqual(info["last_expt"], "IPTS-1234")

        self.assertTrue(self.client.login(username="user1", password="pw"))
        response = self.client.get(url)
        self.assertIn("variables", response.json())
        self.assertIn("data", response.json())

        self.client.logout()
        response = self.client.get(url)
        self.assertEqual(sorted(response.json()), ["das_status", "last_expt", "last_run"])

    def test_instrument_update_from_a_page_gets_401_when_logged_out(self, mock_gethostbyaddr):
        # jQuery marks the page's requests with X-Requested-With
        url = reverse("dasmon:get_update", args=["ref_l"])
        response = self.client.get(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 401)
