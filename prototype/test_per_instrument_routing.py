"""
Unit tests for the per-instrument queue routing prototype.

Reference tests for the prototype in ``states_prototype.py`` (the exploratory
version of the routing logic). The production implementation and its maintained
test suite live in ``src/workflow_app/workflow/`` -- see
``tests/test_per_instrument_routing.py`` there. These prototype tests are kept
for historical context and are not run by CI.

Tests the message routing logic without requiring ActiveMQ infrastructure.
"""

import json
import os
import sys
from unittest.mock import Mock

# The prototype modules live alongside this file; the ``workflow`` package they
# import from lives under src/workflow_app.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "src", "workflow_app"))

from states_prototype import Postprocess_data_ready, StateAction  # noqa: E402


class TestPerInstrumentRouting:
    """Test per-instrument queue routing logic."""

    def test_extract_instrument_from_message(self):
        """Test extracting instrument name from message payload."""
        action = StateAction()
        message = json.dumps({"instrument": "eqsans", "run_number": 12345, "facility": "SNS"})
        assert action.get_instrument_from_message(message) == "eqsans"

    def test_extract_instrument_from_message_uppercase(self):
        """Test instrument extraction handles uppercase."""
        action = StateAction()
        message = json.dumps({"instrument": "EQSANS"})
        assert action.get_instrument_from_message(message) == "eqsans"

    def test_extract_instrument_missing(self):
        """Test handling of message without instrument field."""
        action = StateAction()
        message = json.dumps({"run_number": 12345})
        assert action.get_instrument_from_message(message) is None

    def test_get_instrument_queue_name(self):
        """Test generation of instrument-specific queue names."""
        action = StateAction()
        assert action.get_instrument_queue_name("eqsans", "reduction") == "REDUCTION.EQSANS.DATA_READY"
        assert action.get_instrument_queue_name("venus", "catalog") == "CATALOG.VENUS.DATA_READY"

    def test_postprocess_data_ready_routing(self):
        """Test that messages route to correct per-instrument queue."""
        handler = Postprocess_data_ready(connection=Mock())
        handler.ENABLE_PER_INSTRUMENT_QUEUES = True

        sent_messages = []

        def mock_send(destination, message, persistent="true"):
            sent_messages.append({"destination": destination})

        handler.send = mock_send

        message = json.dumps({"instrument": "cg2", "run_number": 5678, "facility": "HFIR"})
        handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)

        assert len(sent_messages) == 2  # Catalog + Reduction
        reduction_dest = [m for m in sent_messages if "REDUCTION" in m["destination"]][0]
        assert "REDUCTION.CG2.DATA_READY" in reduction_dest["destination"]

    def test_routing_fallback_when_instrument_missing(self):
        """Test fallback to shared queue when instrument is missing."""
        handler = Postprocess_data_ready(connection=Mock())
        handler.ENABLE_PER_INSTRUMENT_QUEUES = True
        handler.USE_SHARED_QUEUE_FALLBACK = True

        sent_messages = []

        def mock_send(destination, message, persistent="true"):
            sent_messages.append({"destination": destination})

        handler.send = mock_send

        message = json.dumps({"run_number": 12345})
        handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)

        reduction_dest = [m for m in sent_messages if "REDUCTION" in m["destination"]][0]
        assert "REDUCTION.DATA_READY" in reduction_dest["destination"]
        assert "REDUCTION.UNKNOWN" not in reduction_dest["destination"]


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
