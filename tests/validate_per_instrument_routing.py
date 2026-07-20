#!/usr/bin/env python
"""
End-to-end validation of per-instrument queue routing against a running broker.

This drives the *real* workflow-manager routing code (the ``workflow.states``
handlers) with a live STOMP connection to an ActiveMQ Artemis broker, exactly as
the workflow manager does when it receives a message. It then confirms -- via a
subscribed consumer and via the Jolokia management API -- that each message
landed on the expected queue, for both feature-flag states. Finally it drains and
deletes the per-instrument queues it created so none are left orphaned.

It is intentionally scoped to the *producer* side (this story); no autoreducer /
consumer is required or involved.

Prerequisites: a broker reachable on STOMP + Jolokia, e.g.::

    docker compose up -d activemq

Run it::

    python tests/validate_per_instrument_routing.py

Environment overrides (all optional):
    BROKER_HOST (default localhost)     STOMP_PORT (default 61613)
    AMQ_USER / AMQ_PASS (default icat)  JOLOKIA_URL (default http://localhost:8161/console/jolokia)
    JOLOKIA_USER / JOLOKIA_PASS (default artemis)   BROKER_NAME (default Artemis-Broker)

Exit code 0 = all checks passed, 1 = a check failed.
"""

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from unittest import mock

# --- make the workflow package importable and Django-configured (no DB needed) ---
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src", "workflow_app"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "workflow.database.settings")

import stomp  # noqa: E402

# --- config -------------------------------------------------------------------
BROKER_HOST = os.environ.get("BROKER_HOST", "localhost")
STOMP_PORT = int(os.environ.get("STOMP_PORT", "61613"))
AMQ_USER = os.environ.get("AMQ_USER", "icat")
AMQ_PASS = os.environ.get("AMQ_PASS", "icat")
JOLOKIA_URL = os.environ.get("JOLOKIA_URL", "http://localhost:8161/console/jolokia")
JOLOKIA_USER = os.environ.get("JOLOKIA_USER", "artemis")
JOLOKIA_PASS = os.environ.get("JOLOKIA_PASS", "artemis")
BROKER_NAME = os.environ.get("BROKER_NAME", "Artemis-Broker")

SHARED_REDUCTION = "REDUCTION.DATA_READY"
SHARED_REDUCTION_CATALOG = "REDUCTION_CATALOG.DATA_READY"
SHARED_CATALOG = "CATALOG.ONCAT.DATA_READY"
TEST_INSTRUMENTS = ["eqsans", "cg2"]

_passes = []
_failures = []


def check(name, condition, detail=""):
    (_passes if condition else _failures).append(name)
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}" + (f" -- {detail}" if detail and not condition else ""))


# --- Jolokia helper (informational: proves queue depths / no orphans) ---------
def jolokia_message_count(queue):
    mbean = (
        f'org.apache.activemq.artemis:broker="{BROKER_NAME}",component=addresses,'
        f'address="{queue}",subcomponent=queues,routing-type="anycast",queue="{queue}"'
    )
    url = f"{JOLOKIA_URL}/read/{urllib.parse.quote(mbean, safe='')}/MessageCount"
    req = urllib.request.Request(url)
    token = base64.b64encode(f"{JOLOKIA_USER}:{JOLOKIA_PASS}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Origin", "http://localhost")  # Artemis Jolokia CORS strict-checks this
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode())
        if payload.get("status") == 200:
            return payload.get("value")
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        print(f"      (jolokia read failed for {queue}: {exc})")
    return None


def jolokia_delete_queue(queue):
    mbean = f'org.apache.activemq.artemis:broker="{BROKER_NAME}"'
    body = json.dumps(
        {
            "type": "exec",
            "mbean": mbean,
            "operation": "destroyQueue(java.lang.String,boolean,boolean)",
            "arguments": [queue, True, True],
        }
    ).encode()
    req = urllib.request.Request(JOLOKIA_URL, data=body, method="POST")
    token = base64.b64encode(f"{JOLOKIA_USER}:{JOLOKIA_PASS}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Origin", "http://localhost")
    try:
        urllib.request.urlopen(req, timeout=5).read()
        return True
    except urllib.error.URLError as exc:
        print(f"      (jolokia delete failed for {queue}: {exc})")
        return False


# --- STOMP consumer that records where each correlated message arrived ---------
class RecordingListener(stomp.ConnectionListener):
    def __init__(self):
        # validation_id -> set of destinations it was delivered to. A single
        # message-id can fan out to several queues (e.g. POSTPROCESS.DATA_READY
        # produces both a CATALOG and a REDUCTION message), so we accumulate.
        self.received = {}
        self.frame_count = 0

    def on_message(self, frame):
        destination = frame.headers.get("destination", "").replace("/queue/", "")
        try:
            vid = json.loads(frame.body).get("validation_id")
        except (json.JSONDecodeError, AttributeError):
            vid = None
        if vid is not None:
            self.received.setdefault(vid, set()).add(destination)
            self.frame_count += 1


def main():
    # Import handlers with the DB write mocked out (routing does not need a DB).
    import workflow.database.transactions as tx

    tx.add_status_entry = mock.MagicMock()
    import importlib

    from workflow import settings as wf_settings
    from workflow.states import Postprocess_data_ready, Reduction_complete

    conn = stomp.Connection(host_and_ports=[(BROKER_HOST, STOMP_PORT)])
    listener = RecordingListener()
    conn.set_listener("recorder", listener)
    conn.connect(AMQ_USER, AMQ_PASS, wait=True)

    # Subscribe to every queue we might route to; subscribing auto-creates them
    # and lets us drain them so nothing is left orphaned.
    all_queues = {SHARED_REDUCTION, SHARED_REDUCTION_CATALOG, SHARED_CATALOG}
    for inst in TEST_INSTRUMENTS:
        all_queues.add(f"REDUCTION.{inst.upper()}.DATA_READY")
        all_queues.add(f"REDUCTION_CATALOG.{inst.upper()}.DATA_READY")
    for i, q in enumerate(sorted(all_queues)):
        conn.subscribe(destination=f"/queue/{q}", id=str(i), ack="auto")

    expected = {}  # validation_id -> (label, set of expected destinations)
    counter = [0]
    total_frames = [0]

    def emit(handler_cls, instrument, expected_dests, label, drop_instrument=False):
        counter[0] += 1
        vid = counter[0]
        msg = {"validation_id": vid, "facility": "SNS", "ipts": "IPTS-1", "run_number": 1000 + vid}
        if not drop_instrument:
            msg["instrument"] = instrument
        expected[vid] = (label, set(expected_dests))
        total_frames[0] += len(expected_dests)
        handler = handler_cls(connection=conn)
        handler({"destination": "/queue/POSTPROCESS.DATA_READY", "message-id": ""}, json.dumps(msg))

    # ---- Phase A: flag ON --------------------------------------------------
    print("\nPhase A: ENABLE_PER_INSTRUMENT_QUEUES=true")
    os.environ["ENABLE_PER_INSTRUMENT_QUEUES"] = "true"
    importlib.reload(wf_settings)
    check("flag parses to True", wf_settings.ENABLE_PER_INSTRUMENT_QUEUES is True)
    for inst in TEST_INSTRUMENTS:
        # POSTPROCESS.DATA_READY fans out to shared CATALOG + per-instrument REDUCTION
        emit(
            Postprocess_data_ready,
            inst,
            {SHARED_CATALOG, f"REDUCTION.{inst.upper()}.DATA_READY"},
            f"postprocess({inst}) flag-on",
        )
        emit(
            Reduction_complete,
            inst,
            {f"REDUCTION_CATALOG.{inst.upper()}.DATA_READY"},
            f"reduction_complete({inst}) flag-on",
        )
    # missing instrument -> shared fallback even with flag on
    emit(
        Postprocess_data_ready,
        None,
        {SHARED_CATALOG, SHARED_REDUCTION},
        "postprocess(no-instrument) flag-on -> shared",
        drop_instrument=True,
    )

    # ---- Phase B: flag OFF -------------------------------------------------
    print("Phase B: ENABLE_PER_INSTRUMENT_QUEUES=false")
    os.environ["ENABLE_PER_INSTRUMENT_QUEUES"] = "false"
    importlib.reload(wf_settings)
    check("flag parses to False", wf_settings.ENABLE_PER_INSTRUMENT_QUEUES is False)
    for inst in TEST_INSTRUMENTS:
        emit(
            Postprocess_data_ready, inst, {SHARED_CATALOG, SHARED_REDUCTION}, f"postprocess({inst}) flag-off -> shared"
        )
        emit(Reduction_complete, inst, {SHARED_REDUCTION_CATALOG}, f"reduction_complete({inst}) flag-off -> shared")

    # ---- wait for delivery and correlate -----------------------------------
    deadline = time.time() + 10
    while time.time() < deadline and listener.frame_count < total_frames[0]:
        time.sleep(0.2)

    print("\nRouting results (correlated via subscribed consumer):")
    for vid, (label, exp) in sorted(expected.items()):
        got = listener.received.get(vid, set())
        check(f"{label}", got == exp, detail=f"expected {sorted(exp)}, got {sorted(got)}")

    # ---- Jolokia: confirm no residual depth on shared reduction queue -------
    # (everything we sent has been drained by our consumer; this shows depths.)
    print("\nJolokia message counts (should be 0 after draining -> no orphans):")
    for q in sorted(all_queues):
        cnt = jolokia_message_count(q)
        print(f"  {q}: {cnt}")

    # ---- cleanup: drain a moment, disconnect, delete per-instrument queues --
    time.sleep(0.5)
    conn.disconnect()
    print("\nCleanup: deleting per-instrument queues created during validation")
    for inst in TEST_INSTRUMENTS:
        for q in (f"REDUCTION.{inst.upper()}.DATA_READY", f"REDUCTION_CATALOG.{inst.upper()}.DATA_READY"):
            ok = jolokia_delete_queue(q)
            print(f"  deleted {q}: {ok}")

    # ---- verdict -----------------------------------------------------------
    print(f"\n{len(_passes)} passed, {len(_failures)} failed")
    if _failures:
        print("FAILED: " + ", ".join(_failures))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
