# third-party imports
from django.conf import settings
import pytest


class TestExtendedDashboard:
    def test_response(self, request_page, HTTPText):
        response = request_page("/dasmon/dashboard/", settings.GENERAL_USER_USERNAME, settings.GENERAL_USER_PASSWORD)
        assert response.ok

        # Check double column of instruments
        text = HTTPText(response.text)
        for side in ["Right", "Left"]:
            assert f"{side} column of instruments" in text


if __name__ == "__main__":
    pytest.main([__file__])
