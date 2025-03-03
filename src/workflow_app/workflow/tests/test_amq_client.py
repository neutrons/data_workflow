from unittest import mock

import pytest
import stomp
from django.test import TestCase

import workflow
from workflow.amq_client import Client

_ = [stomp, workflow]


class Dummy(object):
    def __init__(self, *args, **kwargs) -> None:
        pass


class ClientTest(TestCase):
    @mock.patch("workflow.amq_client.Client.new_connection")
    def test_set_listener(self, mockNewConnection):
        # make a fresh client
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        # mock
        mockNewConnection.return_value = "new_connection"
        # default is None
        self.assertIsNone(client._listener)
        # set listener
        new_listener = mock.Mock()
        new_listener.set_connection = mock.Mock()
        client.set_listener(new_listener)
        # check
        self.assertEqual(client._listener, new_listener)
        mockNewConnection.assert_called()
        new_listener.set_connection.assert_called()

    def test_get_connection(self):
        # --
        # case: connection is None
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        client._connection = None
        # mock
        client.new_connection = mock.Mock()
        client._disconnect = mock.Mock()
        # check
        client.get_connection(consumer_name="test_consumer_name")
        client.new_connection.assert_called()
        client._disconnect.assert_called()
        # --
        # case: connection is not None
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        existing_connection = mock.Mock()
        existing_connection.is_connected = mock.Mock(return_value=True)
        client._connection = existing_connection
        # mock
        client.new_connection = mock.Mock()
        client._disconnect = mock.Mock()
        # check
        client.get_connection(consumer_name="test_consumer_name")
        client.new_connection.assert_not_called()
        client._disconnect.assert_not_called()

    @mock.patch("stomp.Connection")
    def test_new_connection(self, mockConnection):
        # make a fresh client
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        client._consumer_name = "test_consumer_name"
        # mock
        conn = mock.Mock()
        conn.set_listener = mock.Mock()
        conn.connect = mock.Mock()
        mockConnection.return_value = conn
        # check
        # NOTE: use None to trigger the branch for better coverage
        client.new_connection(consumer_name=None)
        conn.set_listener.assert_called()
        conn.connect.assert_called()

    def test_connect(self):
        # make a fresh client
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        client._connection = None  # force trigger branch
        client._queues = "test_queue"
        client._consumer_name = "test_consumer_name"
        client._auto_ack = True
        # mock
        conn = mock.Mock()
        conn.subscribe = mock.Mock()
        client._disconnect = mock.Mock()
        client.get_connection = mock.Mock(return_value=conn)
        # check
        client.connect()
        conn.subscribe.assert_called()
        conn.subscribe.reset_mock()
        conn.subscribe.assert_not_called()
        #
        client._auto_ack = False
        client.connect()
        conn.subscribe.assert_called()

    def test_disconnect(self):
        # make a fresh client
        client = Client(
            brokers=["test_borkers"],
            user="test_user",
            passcode="test_passcode",
            queues="test_queues",  # bypass connecting to backend db for testing
        )
        # mock
        conn = mock.Mock()
        conn.disconnect = mock.Mock()
        client._connection = conn
        # check
        client._disconnect()
        conn.disconnect.assert_called()
        self.assertIsNone(client._connection)

    # NOTE:
    #  verify_workflow is a thin wrapper for workflow_process.WorkflowProcess.

    # NOTE:
    # listen_and_wait is a infinite loop function that is not suitable for unit
    # testing


if __name__ == "__main__":
    pytest.main()
