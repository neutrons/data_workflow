import pytest
from unittest import mock
from django.test import TestCase
import workflow


_ = [workflow]


class WorkflowDaemonTest(TestCase):
    @mock.patch("workflow.amq_listener.Listener")
    @mock.patch("workflow.amq_client.Client")
    def test_run(self, mockClient, mockListener):
        from workflow.sns_post_processing import WorkflowDaemon

        #
        client = mock.MagicMock()
        set_listener = mock.MagicMock()
        client.set_listener.return_value = set_listener
        client.listen_and_wait = mock.MagicMock()
        mockClient = mock.MagicMock()
        mockClient.return_value = client
        listener = mock.MagicMock()
        listener.set_amq_user = mock.MagicMock()
        mockListener = mock.MagicMock()
        mockListener.return_value = listener
        #
        wfdaemon = WorkflowDaemon("pidfile")
        wfdaemon.run()


@mock.patch("workflow.sns_post_processing.WorkflowDaemon")
def test_run_daemon(mockDaemon):
    from workflow.sns_post_processing import run_daemon

    #
    daemon = mock.MagicMock()
    start = mock.MagicMock()
    stop = mock.MagicMock()
    restart = mock.MagicMock()
    daemon.start = start
    daemon.stop = stop
    daemon.restart = restart
    mockDaemon.return_value = daemon
    # case: start
    run_daemon(
        "pidfile",
        "stdout",
        "stderr",
        "check_freq",
        "recover",
        "flexible_tasks",
        command="start",
    )
    start.assert_called()
    # case: stop
    run_daemon(
        "pidfile",
        "stdout",
        "stderr",
        "check_freq",
        "recover",
        "flexible_tasks",
        command="stop",
    )
    stop.assert_called()
    # case: restart
    run_daemon(
        "pidfile",
        "stdout",
        "stderr",
        "check_freq",
        "recover",
        "flexible_tasks",
        command="restart",
    )
    restart.assert_called()


def test_run():
    # NOTE:
    # This func is a user facing command line interface and is not suitable for
    # unit test.
    pass


if __name__ == "__main__":
    pytest.main()
