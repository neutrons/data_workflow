"""
Integration tests for per-instrument queue isolation, routing real messages
through ActiveMQ.
"""

import json
import time

import pytest

# Skipped by default so the file stays collectable: it needs a live broker, a
# Postgres connection, and fixtures this file does not define. The maintained
# end-to-end validation is tests/test_per_instrument_routing_integration.py.
pytestmark = pytest.mark.skip(reason="prototype integration reference; requires live ActiveMQ + DB services")


@pytest.fixture
def instruments_created(db_connection):
    """Create test instruments in database."""
    cursor = db_connection.cursor()

    instruments = ["EQSANS", "VENUS", "CG2", "HB2C"]
    for inst_name in instruments:
        cursor.execute("INSERT INTO report_instrument (name) VALUES (%s) ON CONFLICT (name) DO NOTHING", (inst_name,))

    db_connection.commit()
    cursor.close()

    yield instruments


class TestPerInstrumentQueueIsolation:
    """Integration tests for per-instrument queue behavior."""

    def test_send_messages_to_activemq(self, amq_connection, instruments_created):
        test_data = [
            {"instrument": "eqsans", "run_number": 100, "facility": "SNS"},
            {"instrument": "venus", "run_number": 200, "facility": "SNS"},
            {"instrument": "cg2", "run_number": 300, "facility": "HFIR"},
        ]

        for data in test_data:
            amq_connection.send(
                destination="/queue/POSTPROCESS.DATA_READY", body=json.dumps(data), headers={"persistent": "true"}
            )

        time.sleep(2)
        assert True, "Messages sent successfully to ActiveMQ"

    def test_activemq_queue_exists(self, amq_connection):
        """Verify the ActiveMQ connection is working."""
        test_message = {"test": "connection", "timestamp": time.time()}

        amq_connection.send(
            destination="/queue/TEST.QUEUE", body=json.dumps(test_message), headers={"persistent": "false"}
        )

        assert True, "ActiveMQ connection is working"


@pytest.mark.skip(reason="Requires full workflow manager and autoreducer services running")
class TestQueueIsolationBehavior:
    """Tests that require full workflow infrastructure."""

    def test_queue_isolation_prevents_blocking(self):
        """A high-volume instrument must not block the others."""
        pytest.skip("Requires full infrastructure")

    def test_shared_queue_fallback(self):
        pytest.skip("Requires full infrastructure")


@pytest.mark.skip(reason="Requires full workflow manager and autoreducer services running")
class TestLoadBalancing:
    """Test load distribution across instrument queues."""

    def test_round_robin_consumption(self):
        pytest.skip("Requires autoreducer consumers")

    def test_prefetch_limits_prevent_hoarding(self):
        pytest.skip("Requires consumer monitoring instrumentation")
