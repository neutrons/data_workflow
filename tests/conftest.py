# third-party imports
import pytest

# standard imports
import requests


@pytest.fixture(scope="session")
def request_page():
    r"""Post an HTTP request to a server that requires prior login

    :param subdirectory: requested page, e.g. "/pvmon/arcs/" in URL "http://localhost/users/login?next=/pvmon/arcs/"
    :param username: required for login
    :param password: required for login
    :param domain: domain of the application, default is "localhost",
        e.g. "http://localhost/users/login?next=/pvmon/arcs/"

    :returns requests.Response: server's response to the HTTP request
    """

    def _request_page(subdirectory, username, password, domain="localhost"):
        url = f"http://{domain}/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(url)  # sets the cookie
        csrf_token = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrf_token)
        return client.post(url + subdirectory, data=login_data, timeout=None)

    return _request_page


@pytest.fixture(scope="session")
def HTTPText():
    r"""A class encapsulating a set of helper functions to be applied to an imput HTML string.

    Example:
        text = HTTPText(html_test)
        assert "HTML" in text

    :param str html_text: the input HTML string

    :returns HTTPText object:
    """

    class _HTTPText(object):
        def __init__(self, html_text: str):
            self.text = html_text

        def __contains__(self, substring: str):
            r"""check HTML string contains a substring, but whitespaces are not considered
            :param substring: substring to match
            """
            return substring.replace(" ", "") in self.text.replace(" ", "")

    return _HTTPText
