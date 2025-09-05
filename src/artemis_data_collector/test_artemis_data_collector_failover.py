"""
Unit tests for the Artemis Data Collector with failover support
"""

import unittest
from collections import namedtuple
from unittest.mock import Mock, patch

import requests

from artemis_data_collector.artemis_data_collector import ArtemisDataCollector, parse_args

Config = namedtuple(
    "Config",
    [
        "artemis_user",
        "artemis_password",
        "artemis_url",
        "artemis_failover_url",
        "artemis_broker_name",
        "queue_list",
        "database_hostname",
        "database_port",
        "database_user",
        "database_password",
        "database_name",
        "interval",
    ],
)


class TestArtemisDataCollectorFailover(unittest.TestCase):
    def setUp(self):
        """Set up test configuration with failover URL"""
        self.config = Config(
            "artemis",
            "artemis",
            "http://primary:8161",
            "http://failover:8161",
            "0.0.0.0",
            ["TEST_QUEUE"],
            "localhost",
            5432,
            "workflow",
            "workflow",
            "workflow",
            60,
        )

        self.config_no_failover = Config(
            "artemis",
            "artemis",
            "http://primary:8161",
            None,
            "0.0.0.0",
            ["TEST_QUEUE"],
            "localhost",
            5432,
            "workflow",
            "workflow",
            "workflow",
            60,
        )

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_primary_success(self, mock_session_class, mock_connect):
        """Test successful request to primary broker"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
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
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
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
        result = adc.request_activemq("/test")

        # Should return failover response
        assert result == {"TEST_QUEUE": "data"}
        assert mock_session.get.call_count == 3  # Init call + primary + failover

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_primary_exception_failover_success(self, mock_session_class, mock_connect):
        """Test failover when primary throws exception"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First, mock the get_activemq_queues call (which should succeed for initialization)
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # Then mock test calls: primary throws exception, failover succeeds
        mock_response_failover = Mock()
        mock_response_failover.status_code = 200
        mock_response_failover.json.return_value = {"status": 200, "value": {"TEST_QUEUE": "data"}}

        # Set up the call sequence: init call succeeds, then primary throws exception, then failover succeeds
        mock_session.get.side_effect = [
            mock_response_init,
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response_failover,
        ]

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/test")

        # Should return failover response
        assert result == {"TEST_QUEUE": "data"}
        assert mock_session.get.call_count == 3  # Init call + primary exception + failover

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_no_failover_configured(self, mock_session_class, mock_connect):
        """Test behavior when no failover is configured and primary fails"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First, mock the get_activemq_queues call (which should succeed for initialization)
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # Then mock test call: primary fails
        mock_response_primary = Mock()
        mock_response_primary.status_code = 500  # Primary fails

        # Set up the call sequence: init call succeeds, then primary fails
        mock_session.get.side_effect = [mock_response_init, mock_response_primary]

        adc = ArtemisDataCollector(self.config_no_failover)
        result = adc.request_activemq("/test")

        # Should return None since no failover is configured
        assert result is None
        assert mock_session.get.call_count == 2  # Init call + primary failure

    @patch("artemis_data_collector.artemis_data_collector.psycopg.connect")
    @patch("artemis_data_collector.artemis_data_collector.requests.Session")
    def test_request_activemq_both_fail(self, mock_session_class, mock_connect):
        """Test behavior when both primary and failover fail"""
        # Mock database connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        # First, mock the get_activemq_queues call (which should succeed for initialization)
        mock_response_init = Mock()
        mock_response_init.status_code = 200
        mock_response_init.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # Then mock test calls: both primary and failover fail
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        # Set up the call sequence: init call succeeds, then both primary and failover fail
        mock_session.get.side_effect = [mock_response_init, mock_response_fail, mock_response_fail]

        adc = ArtemisDataCollector(self.config)
        result = adc.request_activemq("/test")

        # Should return None since both fail
        assert result is None
        assert mock_session.get.call_count == 3  # Init call + primary + failover


def test_parse_args_with_failover():
    """Test parsing arguments with failover URL"""
    args = parse_args(["--artemis_failover_url", "http://failover:8161"])
    assert args.artemis_failover_url == "http://failover:8161"


def test_parse_args_with_environment_failover():
    """Test parsing failover URL from environment variable"""
    import os

    os.environ["ARTEMIS_FAILOVER_URL"] = "http://env-failover:8161"
    try:
        args = parse_args([])
        assert args.artemis_failover_url == "http://env-failover:8161"
    finally:
        if "ARTEMIS_FAILOVER_URL" in os.environ:
            del os.environ["ARTEMIS_FAILOVER_URL"]


if __name__ == "__main__":
    unittest.main()
