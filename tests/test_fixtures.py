# third-party imports
from django.conf import settings
import pytest


def test_request_page(request_page):
    response = request_page("/dasmon/", settings.GENERAL_USER_USERNAME, settings.GENERAL_USER_PASSWORD)
    assert response.ok


def test_HTTPText(HTTPText):
    text = HTTPText("on and on")
    assert "on" in text
    assert "ona" in text


if __name__ == "__main__":
    pytest.main([__file__])
