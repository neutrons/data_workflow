import pytest
import httplib2
from unittest import mock

import json
from reporting import dasmon

# print version in case it fails
# NOTE: dasmon do not have a standard version, using dict instead
print(dasmon.__dict__)
print(httplib2.__version__)


@mock.patch("reporting.dasmon.models.LegacyURL.objects")
def test_get_legacy_url(mockLegacyURLObj):
    # patch external dependency
    mockLegacyURLObj.get.return_value = mock.MagicMock()
    mockLegacyURLObj.get.return_value.url = "/test.xyz"

    # test the function
    from reporting.dasmon.legacy_status import get_legacy_url

    url_without_domain = get_legacy_url(instrument_id=1, include_domain=False)
    assert url_without_domain == "/test.xyz"
    url_with_domain = get_legacy_url(instrument_id=1, include_domain=True)
    assert url_with_domain == "http://neutrons.ornl.gov/test.xyz"


@mock.patch("reporting.dasmon.legacy_status.get_legacy_url")
@mock.patch("httplib2.HTTPSConnectionWithTimeout")
def test_get_ops_status(mockHTTPSConnectionWithTimeout, mockGetLegacyUrl):
    # patch the external dependency
    mockHTTPSConnectionWithTimeout.return_value = mock.MagicMock()
    mockHTTPSConnectionWithTimeout.return_value.request = mock.MagicMock()
    mockHTTPSConnectionWithTimeout.return_value.getresponse = mock.MagicMock()
    mockHTTPSConnectionWithTimeout.return_value.getresponse.return_value.read = mock.MagicMock()
    fakeReturnDict = {
        "test1": {"test2": "test3"},
    }
    mockHTTPSConnectionWithTimeout.return_value.getresponse.return_value.read.return_value = json.dumps(fakeReturnDict)
    #
    mockGetLegacyUrl = mock.MagicMock()
    mockGetLegacyUrl.return_value = "/test.xyz"

    # test the function
    from reporting.dasmon.legacy_status import get_ops_status

    data = get_ops_status(instrument_id="PG3")
    assert data == [{"group": "test1", "data": [{"key": "test2", "value": "test3"}]}]


if __name__ == "__main__":
    pytest.main([__file__])
