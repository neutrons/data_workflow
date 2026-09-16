"""
Broker-backed integration tests for per-instrument queue routing.

These drive the *real* workflow-manager handlers (``workflow.states``) over a
live STOMP connection to the ActiveMQ Artemis broker in the docker-compose
stack, then confirm via a subscribed consumer that each message landed on the
queue we expect. They run as part of ``pixi run systemtests``, so the routing
stays exercised instead of relying on a manual script.

Scope notes:

* Only the *per-instrument* queues are driven over the real broker. The shared
  queues (REDUCTION.DATA_READY, CATALOG.ONCAT.DATA_READY) have live consumers in
  the stack, so subscribing to them would compete for real traffic and injecting
  into them would hand the autoreducer runs that do not exist. Those paths are
  asserted against a recording stub connection instead, which is enough: what
  they verify is which destination the handler chose, not broker mechanics.
* ``add_status_entry`` is mocked out. These tests are about routing, not about
  the reporting database, and the workflow container (not this process) owns
  those writes.
* The workflow container in the stack runs with the flag off, which is the
  production default. These tests toggle the flag in-process, which is why they
  instantiate the handlers here rather than sending to POSTPROCESS.DATA_READY
  and waiting for the container to act.
"""

import json
import time
from unittest import mock

import pytest
import stomp
from dotenv import dotenv_values
from workflow.states import Postprocess_data_ready, Reduction_complete, Reduction_request, StateAction

# Instruments used only by these tests. Deliberately not the ones the other
# system tests drive (vulcan, ref_l, arcs, hysa) so nothing collides.
REDUCTION_INSTRUMENT = "eqsans"
HIMEM_INSTRUMENT = "cg2"

PER_INSTRUMENT_QUEUES = [
    "REDUCTION.EQSANS.DATA_READY",
    "REDUCTION_CATALOG.EQSANS.DATA_READY",
    "REDUCTION.HIMEM.CG2.DATA_READY",
]

DELIVERY_TIMEOUT_SECONDS = 15


def _patch_flag(value):
    """Toggle the feature flag; handlers read it from settings at call time."""
    return mock.patch("workflow.settings.ENABLE_PER_INSTRUMENT_QUEUES", value)


class _RecordingListener(stomp.ConnectionListener):
    """Record which queue each correlated message was delivered to."""

    def __init__(self):
        self.received = {}  # validation_id -> set of destinations

    def on_message(self, frame):
        destination = frame.headers.get("destination", "").replace("/queue/", "")
        try:
            validation_id = json.loads(frame.body).get("validation_id")
        except (json.JSONDecodeError, AttributeError):
            return
        if validation_id is not None:
            self.received.setdefault(validation_id, set()).add(destination)

    def wait_for(self, validation_id, timeout=DELIVERY_TIMEOUT_SECONDS):
        """Block until this id has been delivered somewhere, then return where."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if validation_id in self.received:
                # Give a beat for any additional fan-out to the same id.
                time.sleep(0.2)
                return self.received[validation_id]
            time.sleep(0.1)
        return set()


class _StubConnection:
    """Records sends without touching the broker, for the shared-queue paths."""

    def __init__(self):
        self.sent = []

    def send(self, destination, message, persistent="true"):
        self.sent.append(destination)


@pytest.fixture(scope="module")
def routing_consumer():
    """A consumer subscribed to the per-instrument queues these tests create.

    Subscribing before anything is produced also means the queues exist up front,
    so a test never races the broker's auto-create.
    """
    config = dotenv_values(".env")
    assert config
    conn = stomp.Connection(host_and_ports=[("localhost", 61613)])
    listener = _RecordingListener()
    conn.set_listener("per_instrument_routing_recorder", listener)
    conn.connect(config["ICAT_USER"], config["ICAT_PASS"], wait=True)
    for index, queue in enumerate(PER_INSTRUMENT_QUEUES):
        conn.subscribe(destination=f"/queue/{queue}", id=f"per-instrument-{index}", ack="auto")
    yield conn, listener
    conn.disconnect()


@pytest.fixture(scope="module")
def producer_connection():
    """Connection the handlers send through, mirroring the workflow manager."""
    config = dotenv_values(".env")
    assert config
    conn = stomp.Connection(host_and_ports=[("localhost", 61613)])
    conn.connect(config["ICAT_USER"], config["ICAT_PASS"], wait=True)
    yield conn
    conn.disconnect()


@pytest.fixture(autouse=True)
def no_db_writes():
    """Routing is what is under test; the reporting DB writes are not."""
    with mock.patch("workflow.database.transactions.add_status_entry"):
        yield


_next_id = [0]


def _message(instrument=None, validation_id=None):
    _next_id[0] += 1
    payload = {
        "validation_id": validation_id if validation_id is not None else _next_id[0],
        "facility": "SNS",
        "ipts": "IPTS-1234",
        "run_number": 900000 + _next_id[0],
        "data_file": "",
    }
    if instrument is not None:
        payload["instrument"] = instrument
    return payload["validation_id"], json.dumps(payload)


class TestPerInstrumentDeliveryOverBroker:
    """Flag on: messages must physically land on the per-instrument queue."""

    def test_reduction_request_reaches_instrument_queue(self, producer_connection, routing_consumer):
        _conn, listener = routing_consumer
        validation_id, message = _message(REDUCTION_INSTRUMENT)
        with _patch_flag(True):
            Reduction_request(connection=producer_connection)(
                {"destination": "/queue/REDUCTION.REQUEST", "message-id": ""}, message
            )
        assert listener.wait_for(validation_id) == {"REDUCTION.EQSANS.DATA_READY"}

    def test_reduction_complete_reaches_instrument_catalog_queue(self, producer_connection, routing_consumer):
        _conn, listener = routing_consumer
        validation_id, message = _message(REDUCTION_INSTRUMENT)
        with _patch_flag(True):
            Reduction_complete(connection=producer_connection)(
                {"destination": "/queue/REDUCTION.COMPLETE", "message-id": ""}, message
            )
        assert listener.wait_for(validation_id) == {"REDUCTION_CATALOG.EQSANS.DATA_READY"}

    def test_db_task_queue_reaches_instrument_queue_preserving_tier(self, producer_connection, routing_consumer):
        """The path most instruments take: queues configured in the database.

        The high-memory tier segment must survive the split, otherwise enabling
        the flag would silently move HIMEM instruments onto the normal pool.
        """
        _conn, listener = routing_consumer
        validation_id, message = _message(HIMEM_INSTRUMENT)
        task_def = json.dumps({"task_class": "", "task_queues": ["REDUCTION.HIMEM.DATA_READY"]})
        action = StateAction(connection=producer_connection, use_db_task=True)
        with (
            _patch_flag(True),
            mock.patch("workflow.database.transactions.get_task", return_value=task_def),
        ):
            action({"destination": "/queue/POSTPROCESS.DATA_READY", "message-id": ""}, message)
        assert listener.wait_for(validation_id) == {"REDUCTION.HIMEM.CG2.DATA_READY"}


class TestSharedQueuePaths:
    """Paths that must stay on the shared queues, asserted without producing.

    These queues have live consumers in the stack, so the assertion is on the
    destination the handler chose rather than on broker delivery.
    """

    def test_catalog_stays_shared_while_reduction_splits(self):
        connection = _StubConnection()
        _validation_id, message = _message(REDUCTION_INSTRUMENT)
        with _patch_flag(True):
            Postprocess_data_ready(connection=connection)(
                {"destination": "/queue/POSTPROCESS.DATA_READY", "message-id": ""}, message
            )
        assert connection.sent == [
            "/queue/CATALOG.ONCAT.DATA_READY",
            "/queue/REDUCTION.EQSANS.DATA_READY",
        ]

    def test_missing_instrument_falls_back_to_shared(self):
        connection = _StubConnection()
        _validation_id, message = _message(instrument=None)
        with _patch_flag(True):
            Postprocess_data_ready(connection=connection)(
                {"destination": "/queue/POSTPROCESS.DATA_READY", "message-id": ""}, message
            )
        assert connection.sent == [
            "/queue/CATALOG.ONCAT.DATA_READY",
            "/queue/REDUCTION.DATA_READY",
        ]

    def test_flag_off_is_todays_behavior(self):
        connection = _StubConnection()
        _validation_id, message = _message(REDUCTION_INSTRUMENT)
        with _patch_flag(False):
            Postprocess_data_ready(connection=connection)(
                {"destination": "/queue/POSTPROCESS.DATA_READY", "message-id": ""}, message
            )
        assert connection.sent == [
            "/queue/CATALOG.ONCAT.DATA_READY",
            "/queue/REDUCTION.DATA_READY",
        ]
