import pytest
from unittest import mock
from unittest import TestCase
from workflow.daemon import Daemon
import workflow
import os

_ = [os, workflow]


class DaemonTest(TestCase):
    def test_daemonize(self):
        # NOTE: there is no safe to mock system level fork and exit without
        #       messing up the pytest framework.  The original implementation
        #       is not suitable for unit testing.
        pass

    @mock.patch("os.remove")
    def test_delpid(self, mockRemove):
        daemon = Daemon("test_pidfile")
        mockRemove.return_value = mock.Mock()
        # check
        daemon.delpid()
        mockRemove.assert_called()

    def test_start(self):
        daemon = Daemon("test_pidfile")
        # mock
        daemon.daemonize = mock.Mock()
        daemon.run = mock.Mock()
        # check
        daemon.start()
        daemon.daemonize.assert_called()
        daemon.run.assert_called()

    def test_stop(self):
        # cowardly refuse to test the stop function as it involves messing with
        # system level libs within an infinite loop
        pass

    def test_restart(self):
        daemon = Daemon("test_pidfile")
        mock_start = mock.Mock()
        daemon.start = mock_start
        mock_stop = mock.Mock()
        daemon.stop = mock_stop
        # check
        daemon.restart()
        mock_stop.assert_called()
        mock_start.assert_called()

    def test_run(self):
        # the run func is literally empty, nothing to test
        pass


if __name__ == "__main__":
    pytest.main()
