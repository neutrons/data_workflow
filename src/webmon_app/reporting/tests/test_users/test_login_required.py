from unittest import mock

from django.test import TestCase
from django.urls import reverse

# An anonymous request that looks as local as possible: the test client's default
# REMOTE_ADDR of 127.0.0.1, a spoofed X-Real-IP header, and an ORNL reverse-DNS name.
LOCAL_LOOKING = {"HTTP_X_REAL_IP": "127.0.0.1"}


@mock.patch("socket.gethostbyaddr", return_value=("bl4b-ws1.sns.gov", [], ["127.0.0.1"]))
class TestLoginRequired(TestCase):
    def test_ajax_update_needs_login(self, mock_gethostbyaddr):
        for url in (
            reverse("pvmon:get_update", args=["ref_l"]),
            reverse("dasmon:get_update", args=["ref_l"]),
            reverse("report:get_instrument_update", args=["ref_l"]),
        ):
            response = self.client.get(url, **LOCAL_LOOKING)
            self.assertEqual(response.status_code, 401, url)

    def test_pages_redirect_to_login(self, mock_gethostbyaddr):
        for url in (reverse("dasmon:dashboard"), reverse("report:summary")):
            response = self.client.get(url, **LOCAL_LOOKING)
            self.assertEqual(response.status_code, 302, url)
            self.assertEqual(response.url, f"/users/login?next={url}")
