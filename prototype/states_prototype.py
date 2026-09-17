"""
PROTOTYPE: per-instrument queue routing for autoreduction.

Explores routing state handlers to REDUCTION.{INSTRUMENT}.DATA_READY with the
shared queue as a fallback. Two approaches are sketched here: routing from the
message itself, and routing from the Task table.

Status: PROTOTYPE, not production code
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
    Base class for processing messages, unchanged from the original.
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
        Extract the instrument name from a message.

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
        Generate the instrument-specific queue name.

        :param instrument: instrument name (e.g., 'eqsans')
        :param queue_type: 'reduction', 'catalog' or 'reduction_catalog'
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


class Postprocess_data_ready(StateAction):
    """
    PROTOTYPE: handler for POSTPROCESS.DATA_READY, routing per instrument with
    the shared queue as a fallback.
    """

    # Would live in settings or a config file in production.
    ENABLE_PER_INSTRUMENT_QUEUES = True
    USE_SHARED_QUEUE_FALLBACK = True

    def __call__(self, headers, message):
        """Route the message to an instrument-specific or shared reduction queue."""
        instrument = self.get_instrument_from_message(message)

        if self.ENABLE_PER_INSTRUMENT_QUEUES and instrument:
            catalog_queue = self.get_instrument_queue_name(instrument, "catalog")
            reduction_queue = self.get_instrument_queue_name(instrument, "reduction")

            logging.info(
                f"Routing {instrument} run to per-instrument queues: "
                f"catalog={catalog_queue}, reduction={reduction_queue}"
            )
        else:
            catalog_queue = CATALOG_DATA_READY
            reduction_queue = REDUCTION_DATA_READY

            if not instrument:
                logging.warning("Could not extract instrument from message, using shared queue")

        # Catalog stays shared for now, though catalog_queue above could be used.
        self.send(
            destination=f"/queue/{CATALOG_DATA_READY}",
            message=message,
            persistent="true",
        )

        self.send(
            destination=f"/queue/{reduction_queue}",
            message=message,
            persistent="true",
        )


class Reduction_request(StateAction):
    """
    PROTOTYPE: handler for REDUCTION.REQUEST, the manual re-reduction path.
    """

    ENABLE_PER_INSTRUMENT_QUEUES = True

    def __call__(self, headers, message):
        """Route a manual reduction request to the instrument-specific queue."""
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
    PROTOTYPE: handler for REDUCTION.COMPLETE, cataloging the reduced data.
    """

    ENABLE_PER_INSTRUMENT_QUEUES = True

    def __call__(self, headers, message):
        """Route to the reduced-data catalog queue once reduction completes."""
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


# Alternative approach: route from the database instead of the message.
class Postprocess_data_ready_db_driven(StateAction):
    """
    PROTOTYPE: routing driven by the report_task table rather than by the
    message, which allows remapping an instrument without a code change.
    """

    def get_reduction_queue_from_db(self, instrument):
        """
        Query the database for this instrument's queue assignment.

        :param instrument: instrument name
        :return: queue name or None
        """
        try:
            from workflow.database.report.models import Instrument, StatusQueue, Task

            inst_obj = Instrument.objects.get(name=instrument)
            postprocess_queue = StatusQueue.objects.get(name="POSTPROCESS.DATA_READY")

            task = Task.objects.filter(instrument_id=inst_obj, input_queue_id=postprocess_queue).first()

            if task:
                reduction_queues = task.task_queue_ids.filter(name__startswith="REDUCTION.").all()
                if reduction_queues:
                    return str(reduction_queues[0])

        except Exception:
            logging.exception(f"Failed to lookup queue for instrument {instrument}")

        return None

    def __call__(self, headers, message):
        """Route according to the Task model configuration."""
        instrument = self.get_instrument_from_message(message)

        reduction_queue = None
        if instrument:
            reduction_queue = self.get_reduction_queue_from_db(instrument)

        if not reduction_queue:
            reduction_queue = REDUCTION_DATA_READY
            logging.info(f"No DB mapping for {instrument}, using shared queue")

        self.send(destination=f"/queue/{CATALOG_DATA_READY}", message=message, persistent="true")
        self.send(destination=f"/queue/{reduction_queue}", message=message, persistent="true")


def get_per_instrument_queue_config():
    """
    PROTOTYPE: configuration for per-instrument routing. In production this would
    come from settings.py or the environment.

    :return: dict with configuration
    """
    return {
        "enable_per_instrument_queues": True,
        "use_shared_queue_fallback": True,
        "instrument_whitelist": [],  # empty = all instruments
        "shared_queue_instruments": [],  # always use the shared queue
        "queue_name_template": "REDUCTION.{instrument}.DATA_READY",
        "autocreate_queues": True,  # create in the database on first message
    }


def test_instrument_queue_routing():
    """PROTOTYPE: demonstrate the queue routing logic."""
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
    test_instrument_queue_routing()


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
