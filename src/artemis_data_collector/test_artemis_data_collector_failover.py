"""
Test cases for Artemis Data Collector failover functionality
"""

import os

# Add the parent directory to the path to import our module
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .artemis_data_collector import ArtemisDataCollector, parse_args


class TestArtemisDataCollectorFailover(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        # Create a mock config object with the expected attributes from parse_args
        self.config = Mock()
        self.config.artemis_url = "http://primary.broker.example.com:8161"
        self.config.artemis_failover_url = "http://failover.broker.example.com:8161"
        self.config.artemis_user = "admin"
        self.config.artemis_password = "admin"
        self.config.artemis_broker_name = "0.0.0.0"
        self.config.database_hostname = "localhost"
        self.config.database_port = 5432
        self.config.database_user = "workflow"
        self.config.database_password = "workflow"
        self.config.database_name = "workflow"
        self.config.queue_list = ["TEST_QUEUE"]
        self.config.interval = 600
        self.config.log_level = "INFO"
        self.config.log_file = None

    def _create_mock_cursor_context(self, cursor_mock):
        """Helper to create a proper context manager mock for database cursor"""
        cursor_context = MagicMock()
        cursor_context.__enter__ = Mock(return_value=cursor_mock)
        cursor_context.__exit__ = Mock(return_value=None)
        return cursor_context

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_primary_success(self, mock_session_class, mock_connect):
        """Test successful request to primary broker"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value = self._create_mock_cursor_context(mock_cursor)
        mock_connect.return_value = mock_conn

        # Mock successful primary response
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}
        mock_session.get.return_value = mock_response
        mock_session_class.return_value = mock_session

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/AddressNames")

        # Should return primary response without trying failover
        assert result == ["TEST_QUEUE"]
        assert mock_session.get.call_count == 2  # Once for get_activemq_queues, once for our test

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_failover_success(self, mock_session_class, mock_connect):
        """Test failover to secondary broker when primary fails"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value = self._create_mock_cursor_context(mock_cursor)
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First, mock the get_activemq_queues call (which should succeed for initialization)
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # Then mock the test calls: primary fails, failover succeeds
        mock_response_primary = Mock()
        mock_response_primary.status_code = 500  # Primary fails

        mock_response_failover = Mock()
        mock_response_failover.status_code = 200
        mock_response_failover.json.return_value = {"status": 200, "value": {"TEST_QUEUE": "data"}}

        # Set up the call sequence: init call succeeds, then primary fails, then failover succeeds
        mock_session.get.side_effect = [mock_response_init, mock_response_primary, mock_response_failover]

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/QueueNames")

        # Should return failover response
        assert result == {"TEST_QUEUE": "data"}
        assert mock_session.get.call_count == 3  # Init + primary + failover

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    @patch("artemis_data_collector.artemis_data_collector.requests.exceptions.RequestException")
    def test_request_activemq_primary_exception_failover_success(
        self, mock_request_exception, mock_session_class, mock_connect
    ):
        """Test failover when primary throws exception"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value = self._create_mock_cursor_context(mock_cursor)
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First, mock the get_activemq_queues call (which should succeed for initialization)
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # Mock successful failover response
        mock_response_failover = Mock()
        mock_response_failover.status_code = 200
        mock_response_failover.json.return_value = {"status": 200, "value": {"TEST_QUEUE": "exception_test"}}

        # Set up the call sequence: init call succeeds, then primary throws exception, then failover succeeds
        mock_session.get.side_effect = [
            mock_response_init,  # get_activemq_queues
            mock_request_exception("Connection failed"),  # primary fails with exception
            mock_response_failover,  # failover succeeds
        ]

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/QueueNames")

        # Should return failover response
        assert result == {"TEST_QUEUE": "exception_test"}
        assert mock_session.get.call_count == 3  # Init + primary exception + failover

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_no_failover_configured(self, mock_session_class, mock_connect):
        """Test behavior when no failover is configured and primary fails"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value = self._create_mock_cursor_context(mock_cursor)
        mock_connect.return_value = mock_conn

        # Use config without failover
        config_no_failover = Mock()
        config_no_failover.artemis_url = "http://primary.broker.example.com:8161"
        config_no_failover.artemis_failover_url = None  # No failover
        config_no_failover.artemis_user = "admin"
        config_no_failover.artemis_password = "admin"
        config_no_failover.artemis_broker_name = "0.0.0.0"
        config_no_failover.database_hostname = "localhost"
        config_no_failover.database_port = 5432
        config_no_failover.database_user = "workflow"
        config_no_failover.database_password = "workflow"
        config_no_failover.database_name = "workflow"
        config_no_failover.queue_list = ["TEST_QUEUE"]
        config_no_failover.interval = 600
        config_no_failover.log_level = "INFO"
        config_no_failover.log_file = None

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful init, then primary failure
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        mock_response_primary = Mock()
        mock_response_primary.status_code = 500

        mock_session.get.side_effect = [mock_response_init, mock_response_primary]

        adc = ArtemisDataCollector(config_no_failover)
        result = adc.request_activemq("/QueueNames")

        # Should return None when no failover is configured and primary fails
        assert result is None
        assert mock_session.get.call_count == 2  # Init + primary only (no failover attempt)

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_both_fail(self, mock_session_class, mock_connect):
        """Test behavior when both primary and failover fail"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value = self._create_mock_cursor_context(mock_cursor)
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # Mock successful init, then both primary and failover fail
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        mock_response_primary = Mock()
        mock_response_primary.status_code = 500

        mock_response_failover = Mock()
        mock_response_failover.status_code = 500

        mock_session.get.side_effect = [mock_response_init, mock_response_primary, mock_response_failover]

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/QueueNames")

        # Should return None when both fail
        assert result is None
        assert mock_session.get.call_count == 3  # Init + primary + failover


def test_parse_args_with_failover():
    """Test that failover URL can be specified via command line"""
    test_args = [
        "--artemis_url",
        "http://primary.example.com:8161",
        "--artemis_failover_url",
        "http://failover.example.com:8161",
        "--artemis_user",
        "admin",
        "--artemis_password",
        "admin",
        "--queue_list",
        "TESTQ1",
        "TESTQ2",
        "--database_hostname",
        "localhost",
        "--database_name",
        "testdb",
        "--interval",
        "300",
    ]

    args = parse_args(test_args)
    assert args.artemis_failover_url == "http://failover.example.com:8161"


def test_parse_args_with_environment_failover():
    """Test that failover URL can be specified via environment variable"""
    # Set environment variable
    os.environ["ARTEMIS_FAILOVER_URL"] = "http://env.failover.example.com:8161"

    test_args = [
        "--artemis_url",
        "http://primary.example.com:8161",
        "--artemis_user",
        "admin",
        "--artemis_password",
        "admin",
        "--queue_list",
        "TESTQ1",
        "TESTQ2",
        "--database_hostname",
        "localhost",
        "--database_name",
        "testdb",
        "--interval",
        "300",
    ]

    args = parse_args(test_args)
    assert args.artemis_failover_url == "http://env.failover.example.com:8161"

    # Clean up
    del os.environ["ARTEMIS_FAILOVER_URL"]


if __name__ == "__main__":
    unittest.main()
