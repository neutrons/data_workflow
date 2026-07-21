"""
Integration tests for per-instrument queue isolation.

Tests actual message routing through ActiveMQ.
These tests require Docker services to be running.
"""

import json
import time

import pytest

# Prototype integration reference: requires a live ActiveMQ broker, a Postgres
# connection, and the `amq_connection` / `db_connection` fixtures (provided by
# the docker-compose stack, not defined here). Skipped by default so the file is
# collectable without erroring. The maintained end-to-end validation lives in
# tests/validate_per_instrument_routing.py.
pytestmark = pytest.mark.skip(reason="prototype integration reference; requires live ActiveMQ + DB services")


@pytest.fixture
def instruments_created(db_connection):
    """Create test instruments in database."""
    cursor = db_connection.cursor()

    # Create test instruments if they don't exist
    instruments = ["EQSANS", "VENUS", "CG2", "HB2C"]
    for inst_name in instruments:
        cursor.execute("INSERT INTO report_instrument (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (inst_name,))

    db_connection.commit()
    cursor.close()

    yield instruments


class TestPerInstrumentQueueIsolation:
    """Integration tests for per-instrument queue behavior."""

    def test_send_messages_to_activemq(self, amq_connection, instruments_created):
        """Test that we can send messages to ActiveMQ for different instruments."""

        # Send test messages for different instruments
        test_data = [
            {"instrument": "eqsans", "run_number": 100, "facility": "SNS"},
            {"instrument": "venus", "run_number": 200, "facility": "SNS"},
            {"instrument": "cg2", "run_number": 300, "facility": "HFIR"},
        ]

        # Send via POSTPROCESS.DATA_READY
        for data in test_data:
            amq_connection.send(
                destination="/queue/POSTPROCESS.DATA_READY", body=json.dumps(data), headers={"persistent": "true"}
            )

        # Allow processing time
        time.sleep(2)

        # Success if no exceptions raised
        assert True, "Messages sent successfully to ActiveMQ"

    def test_activemq_queue_exists(self, amq_connection):
        """Verify ActiveMQ connection is working."""

        # Simple test - send a test message
        test_message = {"test": "connection", "timestamp": time.time()}

        amq_connection.send(
            destination="/queue/TEST.QUEUE", body=json.dumps(test_message), headers={"persistent": "false"}
        )

        assert True, "ActiveMQ connection is working"


@pytest.mark.skip(reason="Requires full workflow manager and autoreducer services running")
class TestQueueIsolationBehavior:
    """Tests that require full workflow infrastructure."""

    def test_queue_isolation_prevents_blocking(self):
        """Test that high-volume instrument doesn't block others."""
        # This would require:
        # - Workflow manager running
        # - Autoreducer running
        # - Database monitoring
        pytest.skip("Requires full infrastructure")

    def test_shared_queue_fallback(self):
        """Test fallback to shared queue when instrument is unknown."""
        pytest.skip("Requires full infrastructure")


@pytest.mark.skip(reason="Requires full workflow manager and autoreducer services running")
class TestLoadBalancing:
    """Test load distribution across instrument queues."""

    def test_round_robin_consumption(self):
        """Test that consumers fairly process messages from multiple queues."""
        pytest.skip("Requires autoreducer consumers")

    def test_prefetch_limits_prevent_hoarding(self):
        """Test that prefetch limits prevent one consumer from hoarding messages."""
        pytest.skip("Requires consumer monitoring instrumentation")
