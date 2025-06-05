import datetime
from unittest import mock

import pyoncat
import pytest

_ = [pyoncat]


def test_decode_time():
    from reporting.report.catalog import decode_time

    # null case
    rst = decode_time("xxx")
    assert rst is None
    # correct usage
    ts = "2022-01-11T18:10:40.206309+00:00"
    rst = decode_time(ts)
    assert rst == datetime.datetime(2022, 1, 11, 18, 10, 40)


@mock.patch("pyoncat.ONCat")
def test_get_run_info(oncat):
    from reporting.report.catalog import get_run_info

    # make the data
    class dummyObject:
        pass

    datafiles = []
    for i in range(10):
        df = dummyObject()
        df.location = f"tmp/test_{i}.nxs.h5"
        df.metadata = {
            "entry": {
                "title": f"test_{i}",
                "duration": i,
                "total_counts": i**2,
                "proton_charge": i,
                "start_time": "2022-01-11T18:10:40.206309+00:00",
                "end_time": "2022-01-12T18:10:40.206309+00:00",
            }
        }
        df.experiment = "test_exp"
        datafiles.append(df)
    # mocking
    oncat_return = mock.MagicMock()
    oncat_return.login = mock.MagicMock()
    oncat_return.Datafile.list = mock.MagicMock(return_value=datafiles)
    oncat.return_value = oncat_return
    # test
    rst = get_run_info("test_instrument", 123, 1)
    assert len(rst["data_files"]) == 10
    assert rst["proposal"] == "test_exp"


if __name__ == "__main__":
    pytest.main([__file__])
