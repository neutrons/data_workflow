#!/usr/bin/env python3
"""
Integration test script to demonstrate Artemis Data Collector failover functionality.

This script shows how the failover mechanism works by simulating primary broker failures.
"""

import sys
from unittest.mock import Mock, patch

import requests

# Add the source directory to path
sys.path.insert(0, "src")

from artemis_data_collector.artemis_data_collector import ArtemisDataCollector, parse_args


def demo_failover():
    """Demonstrate the failover functionality"""
    print("=== Artemis Data Collector Failover Demo ===\n")

    # Parse configuration with failover
    config = parse_args(
        [
            "--artemis_url",
            "http://primary:8161",
            "--artemis_failover_url",
            "http://failover:8161",
            "--database_hostname",
            "localhost",
            "--queue_list",
            "TEST_QUEUE",
            "--log_level",
            "INFO",
        ]
    )

    print(f"Primary URL: {config.artemis_url}")
    print(f"Failover URL: {config.artemis_failover_url}")
    print()

    # Mock the database and requests to simulate scenarios
    with (
        patch("artemis_data_collector.artemis_data_collector.psycopg.connect") as mock_connect,
        patch("artemis_data_collector.artemis_data_collector.requests.Session") as mock_session_class,
    ):
        # Mock database
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("1", "TEST_QUEUE")]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock session
        mock_session = Mock()
        mock_session_class.return_value = mock_session

        print("Scenario 1: Primary broker working")
        print("-" * 40)

        # Mock successful primary response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}
        mock_session.get.return_value = mock_response

        try:
            adc = ArtemisDataCollector(config)
            result = adc.request_activemq("/AddressNames")
            print(f"✓ Primary broker returned: {result}")
            print(f"  Requests made: {mock_session.get.call_count}")
        except Exception as e:
            print(f"✗ Error: {e}")

        print()

        print("Scenario 2: Primary fails, failover succeeds")
        print("-" * 40)

        # Reset call count
        mock_session.reset_mock()

        # Mock primary failure and failover success
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": 200, "value": ["TEST_QUEUE"]}

        # First call (init) succeeds, second call (primary) fails, third call (failover) succeeds
        mock_session.get.side_effect = [mock_response_success, mock_response_fail, mock_response_success]

        try:
            adc = ArtemisDataCollector(config)
            result = adc.request_activemq("/AddressNames")
            print(f"✓ Failover broker returned: {result}")
            print(f"  Total requests made: {mock_session.get.call_count}")
            print("  → Primary failed, failover succeeded")
        except Exception as e:
            print(f"✗ Error: {e}")

        print()

        print("Scenario 3: Primary fails with connection error, failover succeeds")
        print("-" * 40)

        # Reset call count
        mock_session.reset_mock()

        # Mock connection exception and failover success
        mock_session.get.side_effect = [
            mock_response_success,  # Init call
            requests.exceptions.ConnectionError("Connection failed"),  # Primary fails
            mock_response_success,  # Failover succeeds
        ]

        try:
            adc = ArtemisDataCollector(config)
            result = adc.request_activemq("/AddressNames")
            print(f"✓ Failover broker returned: {result}")
            print(f"  Total requests made: {mock_session.get.call_count}")
            print("  → Primary threw ConnectionError, failover succeeded")
        except Exception as e:
            print(f"✗ Error: {e}")

        print()

        print("Scenario 4: Both primary and failover fail")
        print("-" * 40)

        # Reset call count
        mock_session.reset_mock()

        # Mock both failing
        mock_session.get.side_effect = [
            mock_response_success,  # Init call
            mock_response_fail,  # Primary fails
            mock_response_fail,  # Failover fails
        ]

        try:
            adc = ArtemisDataCollector(config)
            result = adc.request_activemq("/AddressNames")
            print(f"✗ Both brokers failed, result: {result}")
            print(f"  Total requests made: {mock_session.get.call_count}")
            print("  → Both primary and failover failed")
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n=== Demo completed ===")


def demo_configuration():
    """Demonstrate configuration options"""
    print("\n=== Configuration Options Demo ===\n")

    print("Configuration with failover:")
    config_with_failover = parse_args(
        ["--artemis_url", "http://primary:8161", "--artemis_failover_url", "http://failover:8161"]
    )
    print(f"  Primary URL: {config_with_failover.artemis_url}")
    print(f"  Failover URL: {config_with_failover.artemis_failover_url}")

    print("\nConfiguration without failover:")
    config_without_failover = parse_args(["--artemis_url", "http://primary:8161"])
    print(f"  Primary URL: {config_without_failover.artemis_url}")
    print(f"  Failover URL: {config_without_failover.artemis_failover_url}")

    print("\nEnvironment variable configuration:")
    import os

    os.environ["ARTEMIS_FAILOVER_URL"] = "http://env-failover:8161"
    try:
        config_env = parse_args([])
        print(f"  Failover URL from env: {config_env.artemis_failover_url}")
    finally:
        if "ARTEMIS_FAILOVER_URL" in os.environ:
            del os.environ["ARTEMIS_FAILOVER_URL"]


if __name__ == "__main__":
    demo_configuration()
    demo_failover()
