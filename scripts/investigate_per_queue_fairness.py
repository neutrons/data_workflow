#!/usr/bin/env python3
"""
Check whether Artemis takes turns between separate per-queue subscriptions.

One connection subscribes to REDUCTION.CG2.DATA_READY, REDUCTION.EQSANS.DATA_READY and a
shared queue, and handles one message at a time like the post_processing_agent consumer
(ack, then block). CG2 is flooded first, and the delivery order is recorded for each
prefetch header:
  none                no header
  activemq-prefetch-0 activemq.prefetchSize: 0 (what the consumer sends today)
  window-0            consumer-window-size: 0
  window-1            consumer-window-size: 1

Run it with only the broker up, so nothing else consumes the shared queue:
    docker compose up -d activemq
    python scripts/investigate_per_queue_fairness.py --user icat --password icat

--order backlog-first sends the messages before subscribing, like a consumer restart
during a flood.

Exit codes: 0 if at least one variant is fair, 1 if none are, 2 on errors.
"""

import argparse
import base64
import json
import sys
import threading
import time
import urllib.request

import stomp

VARIANTS = {
    "none": {},
    "activemq-prefetch-0": {"activemq.prefetchSize": 0},
    "window-0": {"consumer-window-size": 0},
    "window-1": {"consumer-window-size": 1},
}

CG2_QUEUE = "REDUCTION.CG2.DATA_READY"
EQSANS_QUEUE = "REDUCTION.EQSANS.DATA_READY"
SHARED_QUEUE = "CATALOG.ONCAT.DATA_READY"
LABELS = {CG2_QUEUE: "cg2", EQSANS_QUEUE: "eqsans", SHARED_QUEUE: "shared"}


class Jolokia:
    """Minimal Jolokia client"""

    def __init__(self, host, port, user, password):
        self.url = f"http://{host}:{port}/console/jolokia"
        self.origin = f"http://{host}:{port}"
        self.auth = base64.b64encode(f"{user}:{password}".encode()).decode()
        self.broker = None

    def request(self, body):
        req = urllib.request.Request(
            self.url,
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Origin": self.origin,
                "Authorization": f"Basic {self.auth}",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())

    def find_broker(self):
        """Look up the broker MBean name instead of assuming it"""
        reply = self.request({"type": "search", "mbean": "org.apache.activemq.artemis:broker=*"})
        self.broker = next(name for name in reply["value"] if "," not in name)
        return self.broker

    def queue_names(self):
        reply = self.request({"type": "read", "mbean": self.broker, "attribute": "QueueNames"})
        return sorted(reply["value"])

    def _queue_mbean(self, queue):
        return (
            f'{self.broker},component=addresses,address="{queue}",'
            f'subcomponent=queues,routing-type="anycast",queue="{queue}"'
        )

    def queue_stats(self, queue):
        """Return None if the queue doesn't exist"""
        reply = self.request(
            {
                "type": "read",
                "mbean": self._queue_mbean(queue),
                "attribute": ["MessageCount", "DeliveringCount", "ConsumerCount"],
            }
        )
        return reply["value"] if reply.get("status") == 200 else None

    def purge(self, queue):
        self.request({"type": "exec", "mbean": self._queue_mbean(queue), "operation": "removeAllMessages()"})


class BlockingRecorder(stomp.ConnectionListener):
    """Acks, then blocks the receiver thread like the real consumer"""

    def __init__(self, conn, expected_total, consume_delay_ms):
        self.conn = conn
        self.expected_total = expected_total
        self.consume_delay = consume_delay_ms / 1000.0
        self.received = []
        self._last_msg_time = None
        self._lock = threading.Lock()
        self._done = threading.Event()
        self.broker_error = None

    def on_message(self, frame):
        self.conn.ack(frame.headers["message-id"], frame.headers["subscription"])
        data = json.loads(frame.body)
        with self._lock:
            self.received.append((data["queue"], data["seq"]))
            self._last_msg_time = time.monotonic()
            if len(self.received) >= self.expected_total:
                self._done.set()
        time.sleep(self.consume_delay)

    def on_error(self, frame):
        # The broker sends an ERROR frame when it rejects a subscription, so fail the variant
        self.broker_error = frame.body
        self._done.set()

    def wait(self, total_timeout, idle_timeout):
        """Return once everything has arrived, or after idle_timeout with nothing new"""
        start = time.monotonic()
        while time.monotonic() - start < total_timeout:
            if self._done.wait(timeout=0.25):
                break
            with self._lock:
                last = self._last_msg_time or start
            if time.monotonic() - last > idle_timeout:
                break
        if self.broker_error is not None:
            raise RuntimeError(f"broker error: {self.broker_error}")


def send_batch(conn, queue, count):
    for seq in range(count):
        conn.send(destination=f"/queue/{queue}", body=json.dumps({"queue": queue, "seq": seq}))


def connect(args, listener_factory=None):
    conn = stomp.Connection([(args.host, args.port)])
    listener = None
    if listener_factory is not None:
        listener = listener_factory(conn)
        conn.set_listener("recorder", listener)
    conn.connect(args.user, args.password, wait=True)
    return conn, listener


def run_variant(args, jolokia, name, headers):
    sent = {CG2_QUEUE: args.cg2_count, EQSANS_QUEUE: args.eqsans_count, SHARED_QUEUE: args.shared_count}
    total = sum(sent.values())
    for queue in sent:
        if jolokia.queue_stats(queue) is not None:
            jolokia.purge(queue)

    print(f"\n--- {name}: headers={headers or '{}'} order={args.order} ---")
    producer, _ = connect(args)

    def produce():
        send_batch(producer, CG2_QUEUE, args.cg2_count)
        send_batch(producer, EQSANS_QUEUE, args.eqsans_count)
        send_batch(producer, SHARED_QUEUE, args.shared_count)

    if args.order == "backlog-first":
        produce()
        time.sleep(1.0)

    consumer, recorder = connect(args, lambda c: BlockingRecorder(c, total, args.consume_delay_ms))
    for queue in sent:
        consumer.subscribe(destination=f"/queue/{queue}", id=f"/queue/{queue}", ack="client", headers=headers)
    time.sleep(1.0)

    if args.order == "subscribe-first":
        produce()
    producer.disconnect()

    # With prefetch off, each queue should have at most one message in flight
    time.sleep(2.0)
    in_flight = {LABELS[q]: (jolokia.queue_stats(q) or {}).get("DeliveringCount") for q in sent}

    try:
        recorder.wait(args.timeout, args.idle_timeout)
    finally:
        consumer.disconnect()
    time.sleep(1.0)
    residual = {LABELS[q]: (jolokia.queue_stats(q) or {}).get("MessageCount") for q in sent}
    return analyse(recorder.received, sent, in_flight, residual)


def analyse(received, sent, in_flight, residual):
    order = [LABELS[queue] for queue, _ in received]
    print("  First 30 deliveries: " + " ".join(order[:30]))
    print(f"  In flight per queue after 2 s (DeliveringCount): {in_flight}")

    counts = {label: order.count(label) for label in LABELS.values()}
    expected = {LABELS[queue]: count for queue, count in sent.items()}
    duplicates = len(received) - len(set(received))
    print(f"  Received: {counts} of {expected}, duplicates={duplicates}")
    print(f"  Left in queues after the consumer disconnected: {residual}")

    total = sum(sent.values())
    if len(received) != total or duplicates or any(residual.values()):
        print("  VERDICT: LOSS, DUPLICATION OR UNDELIVERED MESSAGES")
        return False

    # If the queues take turns, the CG2 messages delivered before the last EQSANS (or shared)
    # one should be about the EQSANS count. In arrival order it's the whole flood.
    fair = True
    for victim, count in (("eqsans", sent[EQSANS_QUEUE]), ("shared", sent[SHARED_QUEUE])):
        if not count:
            continue
        first = order.index(victim) + 1
        last = len(order) - order[::-1].index(victim)
        cg2_before_last = order[:last].count("cg2")
        print(f"  {victim}: first at position {first}, last at {last}, CG2 delivered before last = {cg2_before_last}")
        fair = fair and cg2_before_last <= count + 2
    print(f"  VERDICT: {'FAIR (interleaved)' if fair else 'UNFAIR (flood delivered first)'}")
    return fair


def main():
    parser = argparse.ArgumentParser(description="Test Artemis fairness across separate per-queue subscriptions.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=61613)
    parser.add_argument("--console-port", type=int, default=8161)
    parser.add_argument("--user", default="icat")
    parser.add_argument("--password", default="icat")
    parser.add_argument("--cg2-count", type=int, default=100)
    parser.add_argument("--eqsans-count", type=int, default=10)
    parser.add_argument("--shared-count", type=int, default=5, help=f"Messages sent to {SHARED_QUEUE}")
    parser.add_argument("--consume-delay-ms", type=int, default=100, help="Per-message blocking time")
    parser.add_argument("--order", choices=["subscribe-first", "backlog-first"], default="subscribe-first")
    parser.add_argument("--variant", choices=["all", *VARIANTS], default="all")
    parser.add_argument("--timeout", type=int, default=120, help="Max seconds to wait per variant")
    parser.add_argument("--idle-timeout", type=int, default=8, help="Stop after this long with no new message")
    args = parser.parse_args()

    jolokia = Jolokia(args.host, args.console_port, args.user, args.password)
    try:
        print(f"Broker MBean: {jolokia.find_broker()}")
        before = jolokia.queue_names()
    except Exception as exc:
        print(f"ERROR: Jolokia query failed: {exc}", file=sys.stderr)
        return 2
    print(f"Queues on the broker before the test: {before}")

    for queue in LABELS:
        stats = jolokia.queue_stats(queue)
        if stats and stats["ConsumerCount"]:
            print(f"ERROR: {queue} already has {stats['ConsumerCount']} consumer(s); stop them first", file=sys.stderr)
            return 2

    variants = VARIANTS if args.variant == "all" else {args.variant: VARIANTS[args.variant]}
    results = {}
    for name, headers in variants.items():
        try:
            results[name] = run_variant(args, jolokia, name, headers)
        except Exception as exc:
            print(f"ERROR: variant {name} failed: {exc}", file=sys.stderr)
            return 2

    # A wildcard subscription would create an extra queue
    extra = sorted(set(jolokia.queue_names()) - set(before) - set(LABELS))
    print(f"\nQueues created by the test other than the three expected: {extra or 'none'}")
    print("Summary: " + ", ".join(f"{name}={'FAIR' if ok else 'UNFAIR'}" for name, ok in results.items()))
    return 0 if any(results.values()) and not extra else 1


if __name__ == "__main__":
    sys.exit(main())
