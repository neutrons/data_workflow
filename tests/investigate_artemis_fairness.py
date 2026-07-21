#!/usr/bin/env python3
"""
Investigate ActiveMQ Artemis wildcard subscription fairness.

Core question: When an autoreducer subscribes to REDUCTION.*.DATA_READY, does Artemis
deliver from each per-instrument sub-queue fairly (round-robin), or merge in arrival
order (all CG2 first, then EQSANS, defeating per-instrument isolation)?

This replicates the March 2026 incident condition: CG2 floods its queue faster than the
single consumer can process, building a backlog, while EQSANS adds a few runs. We measure
the order in which a wildcard consumer drains that backlog.

Methodology notes (important):
  * The consumer SUBSCRIBES FIRST, then messages are sent. In Artemis a message is routed
    to bound queues at SEND time, so a wildcard queue must exist before messages arrive --
    otherwise they only land in the concrete queues and the wildcard consumer never sees
    them. (This itself is a key operational finding: a wildcard consumer does not
    retroactively pick up a pre-existing backlog.)
  * The consumer is deliberately throttled (--consume-delay-ms) so a backlog forms, which
    is the only condition under which the fairness question is meaningful.
  * Producers send with the /queue/ prefix (anycast), matching the workflow manager.
    The consumer subscribes to the bare address name, matching the post_processing_agent.

Usage:
    docker compose up -d activemq
    python tests/investigate_artemis_fairness.py \\
        --host localhost --port 61613 --user icat --password icat \\
        --cg2-count 100 --eqsans-count 10

Exit codes:
    0  FAIR    -- EQSANS interleaved with CG2 (per-queue fairness)
    1  UNFAIR  -- all CG2 drained before first EQSANS (arrival-order merge)
    2  ERROR   -- connection failure, message loss, or inconclusive result
"""

import argparse
import json
import sys
import threading
import time

import stomp

try:
    import urllib.parse
    import urllib.request

    _HAVE_URLLIB = True
except ImportError:  # pragma: no cover
    _HAVE_URLLIB = False


# ---------------------------------------------------------------------------
# Listener that records delivery order, throttled to force a backlog
# ---------------------------------------------------------------------------


class OrderRecorder(stomp.ConnectionListener):
    def __init__(self, expected_total, consume_delay_ms):
        self.received = []
        self.expected_total = expected_total
        self.consume_delay = consume_delay_ms / 1000.0
        self._last_msg_time = None
        self._lock = threading.Lock()
        self._done = threading.Event()

    def on_message(self, frame):
        # Throttle to simulate slow reduction work, forcing a backlog to build.
        if self.consume_delay:
            time.sleep(self.consume_delay)
        try:
            data = json.loads(frame.body)
            instrument = data.get("instrument", "unknown")
        except (json.JSONDecodeError, AttributeError):
            instrument = "parse-error"
        with self._lock:
            self.received.append(instrument)
            self._last_msg_time = time.monotonic()
            if len(self.received) >= self.expected_total:
                self._done.set()

    def on_error(self, frame):
        print(f"ERROR from broker: {frame.body}", file=sys.stderr)

    def wait_until_complete_or_idle(self, total_timeout, idle_timeout):
        """Return when all expected messages arrive, or no message for idle_timeout."""
        deadline = time.monotonic() + total_timeout
        while time.monotonic() < deadline:
            if self._done.wait(timeout=0.25):
                return
            with self._lock:
                last = self._last_msg_time
            if last is not None and (time.monotonic() - last) > idle_timeout:
                return


# ---------------------------------------------------------------------------
# Management API helper (Jolokia) to read residual queue depths
# ---------------------------------------------------------------------------


def read_queue_count(console_host, console_port, user, password, address, queue):
    """Return MessageCount for an anycast queue, or None if unavailable."""
    if not _HAVE_URLLIB:
        return None
    addr_enc = urllib.parse.quote(address, safe="")
    queue_enc = urllib.parse.quote(queue, safe="")
    mbean = (
        f"org.apache.activemq.artemis:broker=%22Artemis-Broker%22,"
        f"component=addresses,address=%22{addr_enc}%22,"
        f"subcomponent=queues,routing-type=%22anycast%22,queue=%22{queue_enc}%22"
    )
    url = f"http://{console_host}:{console_port}/console/jolokia/read/{mbean}/MessageCount"
    req = urllib.request.Request(url, headers={"Origin": f"http://{console_host}:{console_port}"})
    import base64

    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    req.add_header("Authorization", f"Basic {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = json.loads(resp.read().decode())
            return payload.get("value")
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------


def send_batch(conn, queue, instrument, count, run_number_start):
    for i in range(count):
        payload = json.dumps(
            {
                "instrument": instrument,
                "run_number": run_number_start + i,
                "facility": "SNS",
                "data_file": (
                    f"/SNS/{instrument.upper()}/IPTS-9999/nexus/{instrument.upper()}_{run_number_start + i}.nxs.h5"
                ),
            }
        )
        conn.send(destination=queue, body=payload, headers={"persistent": "false"})


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def analyse(received, cg2_count, eqsans_count, residual):
    total = len(received)
    print(f"\nReceived {total} of {cg2_count + eqsans_count} messages via wildcard consumer")
    print(f"\nFirst {min(40, total)} deliveries (in order):")
    for i, inst in enumerate(received[:40]):
        marker = "  <-- EQSANS" if inst == "eqsans" else ""
        print(f"  {i + 1:3d}. {inst}{marker}")
    if total > 40:
        print(f"  ... ({total - 40} more)")

    cg2_received = received.count("cg2")
    eqsans_received = received.count("eqsans")
    first_eqsans_pos = next((i for i, inst in enumerate(received) if inst == "eqsans"), None)

    print("\nSummary:")
    print(f"  CG2    received via wildcard : {cg2_received} / {cg2_count}")
    print(f"  EQSANS received via wildcard : {eqsans_received} / {eqsans_count}")
    if residual:
        print("  Residual left in CONCRETE queues (no wildcard delivery):")
        for name, count in residual.items():
            print(f"    {name}: {count}")

    # Message-loss / split-routing check
    if total < cg2_count + eqsans_count:
        print(
            "\nVERDICT: SPLIT ROUTING / MESSAGE LOSS\n"
            f"  The wildcard consumer received only {total} of {cg2_count + eqsans_count} messages.\n"
            "  Artemis anycast load-balanced messages BETWEEN the concrete per-instrument queue\n"
            "  and the wildcard queue. Messages sent to the concrete queue have no consumer and\n"
            "  sit undelivered. A wildcard anycast subscription does NOT reliably receive every\n"
            "  message -- this is a correctness problem, separate from fairness."
        )
        return 2

    if first_eqsans_pos is None:
        print("\nVERDICT: INCONCLUSIVE -- no EQSANS messages received")
        return 2

    print(f"  First EQSANS appeared at delivery position : {first_eqsans_pos + 1} of {total}")

    if first_eqsans_pos < cg2_count:
        print(
            "\nVERDICT: FAIR\n"
            "  EQSANS messages were interleaved before the CG2 backlog drained.\n"
            "  Per-instrument queue isolation + wildcard subscription prevents blocking."
        )
        return 0
    else:
        print(
            "\nVERDICT: UNFAIR (arrival-order merge)\n"
            f"  All {cg2_count} CG2 messages were delivered before the first EQSANS message.\n"
            "  The wildcard subscription merges per-instrument queues into one arrival-ordered\n"
            "  stream. Per-instrument isolation does NOT solve the March 2026 blocking problem;\n"
            "  an alternative fairness mechanism is required (e.g. one consumer per queue)."
        )
        return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Test whether Artemis wildcard subscriptions deliver per-queue fairly."
    )
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=61613)
    parser.add_argument(
        "--console-port", type=int, default=8161, help="Artemis web console port for management API queries"
    )
    parser.add_argument("--user", default="icat")
    parser.add_argument("--password", default="icat")
    parser.add_argument("--cg2-count", type=int, default=100, help="Number of CG2 messages to flood")
    parser.add_argument(
        "--eqsans-count", type=int, default=10, help="Number of EQSANS messages to send after the CG2 flood"
    )
    parser.add_argument(
        "--consume-delay-ms",
        type=int,
        default=30,
        help="Per-message processing delay to force a backlog (default 30ms)",
    )
    parser.add_argument("--timeout", type=int, default=120, help="Max seconds to wait for delivery")
    parser.add_argument(
        "--idle-timeout", type=int, default=8, help="Stop waiting after this many seconds with no new message"
    )
    args = parser.parse_args()

    cg2_concrete = "REDUCTION.CG2.DATA_READY"
    eqsans_concrete = "REDUCTION.EQSANS.DATA_READY"
    cg2_queue = f"/queue/{cg2_concrete}"
    eqsans_queue = f"/queue/{eqsans_concrete}"
    wildcard_dest = "REDUCTION.*.DATA_READY"  # bare name, matches post_processing_agent
    total_expected = args.cg2_count + args.eqsans_count

    print("=" * 72)
    print("Artemis Wildcard Subscription Fairness Investigation")
    print("=" * 72)
    print(f"  Broker        : {args.host}:{args.port}")
    print(f"  CG2 flood     : {args.cg2_count} messages -> {cg2_queue}")
    print(f"  EQSANS        : {args.eqsans_count} messages -> {eqsans_queue} (after CG2)")
    print(f"  Consumer      : subscribe '{wildcard_dest}' FIRST, {args.consume_delay_ms}ms/msg")
    print()

    # -- Step 1: Subscribe to the wildcard FIRST (establishes the binding) --
    print(f"Step 1: Subscribing to '{wildcard_dest}' (slow consumer) ...")
    recorder = OrderRecorder(total_expected, args.consume_delay_ms)
    consumer = stomp.Connection([(args.host, args.port)])
    consumer.set_listener("recorder", recorder)
    try:
        consumer.connect(args.user, args.password, wait=True)
    except Exception as exc:
        print(f"ERROR: consumer could not connect: {exc}", file=sys.stderr)
        return 2
    consumer.subscribe(destination=wildcard_dest, id="fairness-test", ack="auto")
    time.sleep(1.0)  # let the binding settle before producing

    # -- Step 2: Flood CG2, then send EQSANS --------------------------------
    print(f"Step 2: Flooding {args.cg2_count} CG2 then {args.eqsans_count} EQSANS ...")
    producer = stomp.Connection([(args.host, args.port)])
    try:
        producer.connect(args.user, args.password, wait=True)
    except Exception as exc:
        print(f"ERROR: producer could not connect: {exc}", file=sys.stderr)
        consumer.disconnect()
        return 2
    send_batch(producer, cg2_queue, "cg2", args.cg2_count, run_number_start=10000)
    send_batch(producer, eqsans_queue, "eqsans", args.eqsans_count, run_number_start=20000)
    producer.disconnect()
    print("  All messages sent.")

    # -- Step 3: Drain and record order -------------------------------------
    print(f"Step 3: Recording delivery order (timeout {args.timeout}s, idle {args.idle_timeout}s) ...")
    recorder.wait_until_complete_or_idle(args.timeout, args.idle_timeout)
    consumer.disconnect()

    # -- Step 4: Read residual depth in concrete queues ---------------------
    residual = {}
    for name in (cg2_concrete, eqsans_concrete):
        count = read_queue_count(args.host, args.console_port, args.user, args.password, name, name)
        if count is not None:
            residual[name] = count

    # -- Step 5: Analyse ----------------------------------------------------
    return analyse(recorder.received, args.cg2_count, args.eqsans_count, residual)


if __name__ == "__main__":
    sys.exit(main())
