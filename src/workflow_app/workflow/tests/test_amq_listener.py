import pytest
from unittest import mock
from django.test import TestCase
import stomp
import workflow
from workflow.amq_listener import Listener

_ = [stomp, workflow]


class ListenerTest(TestCase):
    def test_set_amq_user(self):
        # make a fresh listener
        listener = Listener()
        #
        listener.set_amq_user(
            brokers="test_broker",
            user="test_user",
            passcode="test_passcode",
        )
        self.assertEqual(listener._brokers, "test_broker")
        self.assertEqual(listener._user, "test_user")
        self.assertEqual(listener._passcode, "test_passcode")

    def test_on_message(self):
        callfunc = mock.MagicMock()
        with mock.patch("workflow.states.StateAction", return_value=callfunc):
            listener = Listener()
            # mock
            conn = mock.Mock()
            conn.ack = mock.Mock()
            listener._get_connection = mock.Mock(return_value=conn)
            frame = mock.Mock()
            frame.headers = {"destination": "test_value"}
            frame.body = "test_body"
            # check
            listener.on_message(frame)
            callfunc.assert_called()

    def test_set_connection(self):
        # make a fresh listener
        listener = Listener()
        # check
        listener.set_connection(connection="test_connection")
        self.assertEqual(listener._send_connection, "test_connection")

    @mock.patch("stomp.Connection")
    def test_get_connection(self, mockConnection):
        conn = mock.MagicMock()
        conn.connect = mock.Mock()
        mockConnection.return_value = conn
        # make a fresh listener
        listener = Listener()
        # check
        listener._send_connection = None
        rst = listener._get_connection()
        self.assertIsNotNone(rst)


if __name__ == "__main__":
    pytest.main()
