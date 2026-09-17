"""
Reference tests for the routing prototype in ``states_prototype.py``. Kept for
historical context and not run by CI; the maintained suite lives in
``src/workflow_app/workflow/tests/test_per_instrument_routing.py``.
"""

import json
import os
import sys
from unittest.mock import Mock

# The prototype modules sit beside this file; ``workflow`` lives under src/.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "src", "workflow_app"))

from states_prototype import Postprocess_data_ready, StateAction  # noqa: E402


class TestPerInstrumentRouting:
    def test_extract_instrument_from_message(self):
        action = StateAction()
        message = json.dumps({"instrument": "eqsans", "run_number": 12345, "facility": "SNS"})
        assert action.get_instrument_from_message(message) == "eqsans"

    def test_extract_instrument_from_message_uppercase(self):
        action = StateAction()
        message = json.dumps({"instrument": "EQSANS"})
        assert action.get_instrument_from_message(message) == "eqsans"

    def test_extract_instrument_missing(self):
        action = StateAction()
        message = json.dumps({"run_number": 12345})
        assert action.get_instrument_from_message(message) is None

    def test_get_instrument_queue_name(self):
        action = StateAction()
        assert action.get_instrument_queue_name("eqsans", "reduction") == "REDUCTION.EQSANS.DATA_READY"
        assert action.get_instrument_queue_name("venus", "catalog") == "CATALOG.VENUS.DATA_READY"

    def test_postprocess_data_ready_routing(self):
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
