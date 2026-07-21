"""
PROTOTYPE: Per-Instrument Queue Routing for Autoreduction

This file demonstrates the proposed changes to enable per-instrument queue isolation.
It shows how to modify state handlers to route messages to instrument-specific queues.

Key Changes:
1. Extract instrument from message data
2. Route to instrument-specific queue: REDUCTION.{INSTRUMENT}.DATA_READY
3. Maintain backward compatibility with shared queue as fallback
4. Support both static and dynamic queue creation

Status: PROTOTYPE - Not production code
Date: April 17, 2026
Related: EWM-15518, EWM-15444
"""

import json
import logging

from workflow.database import transactions
from workflow.settings import (
    CATALOG_DATA_READY,
    POSTPROCESS_ERROR,
    REDUCTION_CATALOG_DATA_READY,
    REDUCTION_DATA_READY,
)


class StateAction:
    """
    Base class for processing messages (unchanged from original)
    """

    _send_connection = None

    def __init__(self, connection=None, use_db_task=False):
        self._user_db_task = use_db_task
        self._send_connection = connection

    def send(self, destination, message, persistent="true"):
        """Send a message to a queue"""
        logging.debug("Send: %s" % destination)
        if self._send_connection is not None:
            self._send_connection.send(destination, message, persistent=persistent)
            headers = {"destination": destination, "message-id": ""}
            transactions.add_status_entry(headers, message)
        else:
            logging.error("No AMQ connection to send to %s" % destination)
            headers = {"destination": "/queue/%s" % POSTPROCESS_ERROR, "message-id": ""}
            data_dict = json.loads(message)
            data_dict["error"] = "No AMQ connection: Could not send to %s" % destination
            message = json.dumps(data_dict)
            transactions.add_status_entry(headers, message)

    def get_instrument_from_message(self, message):
        """
        Extract instrument name from message.

        :param message: JSON-encoded message content
        :return: lowercase instrument name or None
        """
        try:
            data = json.loads(message)
            if "instrument" in data:
                return data["instrument"].lower()
        except (json.JSONDecodeError, KeyError, AttributeError):
            logging.exception("Failed to extract instrument from message")
        return None

    def get_instrument_queue_name(self, instrument, queue_type="reduction"):
        """
        Generate instrument-specific queue name.

        :param instrument: instrument name (e.g., 'eqsans')
        :param queue_type: type of queue ('reduction', 'catalog', etc.)
        :return: queue name string
        """
        instrument_upper = instrument.upper()

        if queue_type == "reduction":
            return f"REDUCTION.{instrument_upper}.DATA_READY"
        elif queue_type == "catalog":
            return f"CATALOG.{instrument_upper}.DATA_READY"
        elif queue_type == "reduction_catalog":
            return f"REDUCTION_CATALOG.{instrument_upper}.DATA_READY"
        else:
            raise ValueError(f"Unknown queue type: {queue_type}")


# ============================================================================
# PROTOTYPE: Enhanced State Handlers with Per-Instrument Routing
# ============================================================================


class Postprocess_data_ready(StateAction):
    """
    PROTOTYPE: Enhanced handler for POSTPROCESS.DATA_READY messages.

    Routes to instrument-specific queues instead of shared queue.
    Maintains backward compatibility via fallback to shared queue.
    """

    # Configuration flags (would be in settings or config file in production)
    ENABLE_PER_INSTRUMENT_QUEUES = True  # Toggle per-instrument routing
    USE_SHARED_QUEUE_FALLBACK = True  # Fallback to shared queue if instrument unknown

    def __call__(self, headers, message):
        """
        Route message to instrument-specific or shared reduction queue.

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        instrument = self.get_instrument_from_message(message)

        # Determine catalog and reduction queue destinations
        if self.ENABLE_PER_INSTRUMENT_QUEUES and instrument:
            # Per-instrument routing
            catalog_queue = self.get_instrument_queue_name(instrument, "catalog")
            reduction_queue = self.get_instrument_queue_name(instrument, "reduction")

            logging.info(
                f"Routing {instrument} run to per-instrument queues: "
                f"catalog={catalog_queue}, reduction={reduction_queue}"
            )
        else:
            # Fallback to shared queues
            catalog_queue = CATALOG_DATA_READY
            reduction_queue = REDUCTION_DATA_READY

            if not instrument:
                logging.warning("Could not extract instrument from message, using shared queue")

        # Send to catalog queue (could also be per-instrument in future)
        # NOTE: Keeping catalog as shared queue for now, but could also be per-instrument
        self.send(
            destination=f"/queue/{CATALOG_DATA_READY}",  # Could use catalog_queue for per-inst
            message=message,
            persistent="true",
        )

        # Send to reduction queue (per-instrument or shared)
        self.send(
            destination=f"/queue/{reduction_queue}",
            message=message,
            persistent="true",
        )


class Reduction_request(StateAction):
    """
    PROTOTYPE: Enhanced handler for REDUCTION.REQUEST messages.

    Supports manual reduction requests with per-instrument routing.
    """

    ENABLE_PER_INSTRUMENT_QUEUES = True

    def __call__(self, headers, message):
        """
        Route reduction request to instrument-specific queue.

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        instrument = self.get_instrument_from_message(message)

        if self.ENABLE_PER_INSTRUMENT_QUEUES and instrument:
            reduction_queue = self.get_instrument_queue_name(instrument, "reduction")
            logging.info(f"Manual reduction request for {instrument} → {reduction_queue}")
        else:
            reduction_queue = REDUCTION_DATA_READY
            if not instrument:
                logging.warning("Could not extract instrument from reduction request, using shared queue")

        self.send(
            destination=f"/queue/{reduction_queue}",
            message=message,
            persistent="true",
        )


class Reduction_complete(StateAction):
    """
    PROTOTYPE: Enhanced handler for REDUCTION.COMPLETE messages.

    Routes completed reduction to instrument-specific catalog queue.
    """

    ENABLE_PER_INSTRUMENT_QUEUES = True

    def __call__(self, headers, message):
        """
        Route to catalog reduced data queue after reduction completes.

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        instrument = self.get_instrument_from_message(message)

        if self.ENABLE_PER_INSTRUMENT_QUEUES and instrument:
            catalog_queue = self.get_instrument_queue_name(instrument, "reduction_catalog")
            logging.info(f"Reduction complete for {instrument} → {catalog_queue}")
        else:
            catalog_queue = REDUCTION_CATALOG_DATA_READY

        self.send(
            destination=f"/queue/{catalog_queue}",
            message=message,
            persistent="true",
        )


# ============================================================================
# Database-Driven Queue Routing (Alternative Approach)
# ============================================================================


class Postprocess_data_ready_db_driven(StateAction):
    """
    PROTOTYPE: Database-driven routing using existing Task model.

    This approach leverages the report_task table to map instruments to queues,
    providing more flexibility without code changes.
    """

    def get_reduction_queue_from_db(self, instrument):
        """
        Query database for instrument-specific queue assignment.

        :param instrument: instrument name
        :return: queue name or None
        """
        try:
            # This would query the Task model for instrument-specific routing
            # Simplified example (actual implementation in transactions.py):
            from workflow.database.report.models import Instrument, StatusQueue, Task

            inst_obj = Instrument.objects.get(name=instrument)
            postprocess_queue = StatusQueue.objects.get(name="POSTPROCESS.DATA_READY")

            # Find task mapping for this instrument + input queue
            task = Task.objects.filter(instrument_id=inst_obj, input_queue_id=postprocess_queue).first()

            if task:
                # Get output queues for reduction
                reduction_queues = task.task_queue_ids.filter(name__startswith="REDUCTION.").all()
                if reduction_queues:
                    return str(reduction_queues[0])  # Return first reduction queue

        except Exception:
            logging.exception(f"Failed to lookup queue for instrument {instrument}")

        return None

    def __call__(self, headers, message):
        """
        Route based on database Task model configuration.

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        instrument = self.get_instrument_from_message(message)

        # Try database lookup first
        reduction_queue = None
        if instrument:
            reduction_queue = self.get_reduction_queue_from_db(instrument)

        # Fallback to default shared queue
        if not reduction_queue:
            reduction_queue = REDUCTION_DATA_READY
            logging.info(f"No DB mapping for {instrument}, using shared queue")

        # Send to catalog (shared) and reduction (per-instrument or shared)
        self.send(destination=f"/queue/{CATALOG_DATA_READY}", message=message, persistent="true")
        self.send(destination=f"/queue/{reduction_queue}", message=message, persistent="true")


# ============================================================================
# Configuration Management
# ============================================================================


def get_per_instrument_queue_config():
    """
    PROTOTYPE: Configuration for per-instrument queue routing.

    In production, this would be loaded from settings.py or environment variables.

    :return: dict with configuration
    """
    return {
        # Enable per-instrument routing globally
        "enable_per_instrument_queues": True,
        # Fallback to shared queue if instrument unknown
        "use_shared_queue_fallback": True,
        # List of instruments to route to per-instrument queues
        # (empty list = all instruments)
        "instrument_whitelist": [],
        # List of instruments to always use shared queue
        "shared_queue_instruments": [],
        # Queue naming convention
        "queue_name_template": "REDUCTION.{instrument}.DATA_READY",
        # Auto-create queues in database on first message
        "autocreate_queues": True,
    }


# ============================================================================
# Testing Utilities
# ============================================================================


def test_instrument_queue_routing():
    """
    PROTOTYPE: Test function demonstrating queue routing logic.
    """
    test_messages = [
        {
            "instrument": "eqsans",
            "facility": "SNS",
            "ipts": "IPTS-1234",
            "run_number": 12345,
            "data_file": "/SNS/EQSANS/IPTS-1234/nexus/EQSANS_12345.nxs.h5",
        },
        {
            "instrument": "venus",
            "facility": "SNS",
            "ipts": "IPTS-5678",
            "run_number": 5678,
            "data_file": "/SNS/VENUS/IPTS-5678/nexus/VENUS_5678.nxs.h5",
        },
        {
            "instrument": "cg2",
            "facility": "HFIR",
            "ipts": "IPTS-9999",
            "run_number": 9999,
            "data_file": "/HFIR/CG2/IPTS-9999/nexus/CG2_9999.nxs.h5",
        },
    ]

    handler = Postprocess_data_ready(connection=None)

    print("Testing Per-Instrument Queue Routing")
    print("=" * 60)

    for msg_data in test_messages:
        message = json.dumps(msg_data)
        instrument = handler.get_instrument_from_message(message)
        reduction_queue = handler.get_instrument_queue_name(instrument, "reduction")

        print(f"\nInstrument: {instrument.upper()}")
        print(f"  Reduction Queue: {reduction_queue}")
        print(f"  Run Number: {msg_data['run_number']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Run test demonstration
    test_instrument_queue_routing()


# ============================================================================
# Migration Notes
# ============================================================================

_MIGRATION_NOTES = """
IMPLEMENTATION CHECKLIST:

1. Code Changes:
   ✓ Modify Postprocess_data_ready handler to use per-instrument routing
   ✓ Modify Reduction_request handler similarly
   ✓ Modify Reduction_complete handler for catalog routing
   ✓ Add configuration flags to settings.py
   ✓ Add helper methods to StateAction base class

2. Database Changes:
   ✓ Create Task entries for each instrument mapping to per-instrument queues
   ✓ OR: Auto-create StatusQueue entries when first message arrives
   ✓ Add database migration to populate initial instrument→queue mappings

3. ActiveMQ Configuration:
   ✓ Enable auto-create-queues in broker.xml (already enabled)
   ✓ OR: Pre-create per-instrument queues via admin console
   ✓ Configure queue policies (max depth, expiry, DLQ)

4. Autoreducer Configuration:
   ✓ Update post_process_consumer.conf to subscribe to multiple queues
   ✓ OR: Use wildcard subscription: REDUCTION.*.DATA_READY
   ✓ Change ack mode from "auto" to "client" for reliability

5. Monitoring:
   ✓ Add per-instrument queue depth metrics to dashboard
   ✓ Add alerts for per-instrument queue depth > threshold
   ✓ Add worker utilization per instrument metrics

6. Testing:
   ✓ Update webmonchow to route to per-instrument queues
   ✓ Create integration tests for queue isolation
   ✓ Load test with multiple instruments at different rates
   ✓ Verify backward compatibility with shared queue

7. Documentation:
   ✓ Update architecture docs with new queue topology
   ✓ Update admin docs for adding new instruments
   ✓ Update troubleshooting docs for queue-related issues
   ✓ Create migration guide for deployment

BACKWARD COMPATIBILITY:

- Keep REDUCTION.DATA_READY as fallback/default queue
- Support gradual migration: some instruments per-instrument, others shared
- Configuration flag to disable per-instrument routing if issues arise
- Graceful degradation: if instrument unknown, route to shared queue

PERFORMANCE CONSIDERATIONS:

- Queue lookup overhead: Minimal (in-memory operation or single DB query)
- Message routing: No change in latency (same STOMP send operation)
- Queue proliferation: Plan for 20-30 queues (one per active instrument)
- Monitoring overhead: Track O(N) queues instead of O(1), negligible impact

SECURITY CONSIDERATIONS:

- Queue naming must prevent injection attacks (validate instrument names)
- Access control: Same permissions as current shared queue
- Message integrity: No changes to message format or encryption
"""
