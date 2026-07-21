#!/usr/bin/env python3
"""
Baseline profiling harness for the autoreduction queue.

This drives a controlled, reproducible workload through the *current* shared
queue (or the per-instrument queues, depending on configuration) and then
measures it with :mod:`metrics`. Unlike the older load-test script it does not
blindly ``sleep(30)`` - it waits for the work to actually drain by polling the
database, then reports the three metrics.

Run (with the stack up via ``docker compose up -d``)::

    .pixi/envs/default/bin/python tests/profiling/baseline_profile.py \\
        --scenario blocking --capacity 10

Scenarios:
    blocking      - 200 CG2 runs flood, then 10 EQSANS runs (March 2026 incident)
    large-dataset - 1 VENUS "large" run alongside normal runs from 3 instruments
    fairness      - 20 interleaved batches across 5 instruments

Notes:
  * For a clean baseline, pause the noise generator first:
        docker compose stop webmonchow
  * "capacity" is autoreducer nodes * max_procs. The default stack is
    2 nodes (autoreducer + autoreducer_himem) * max_procs 5 = 10.
"""

import argparse
import os
import sys
import time

# Reuse the STOMP sender from the sibling load-test module rather than
# duplicating connection/send code.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_test_per_instrument_queues import LoadTestClient  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import metrics  # noqa: E402

# Each scenario is an ordered list of phases. A phase sends ``count`` runs for
# ``instrument`` starting at run number ``base``. Order matters: the first phase
# is sent first and creates the backlog.
# Real data files baked into the autoreducer image (SNSdata.tar.gz). A run only
# occupies a worker if its data_file exists in the container; arbitrary files
# error out instantly at the post-process stage. For controlled processing time
# the flood/victim instruments' reduce scripts are replaced with a fixed sleep
# (see METHODOLOGY.md "Controlled processing time").
ARCS_FILE = "/SNS/ARCS/IPTS-27800/nexus/ARCS_214583.nxs.h5"
REF_L_FILE = "/SNS/REF_L/IPTS-33077/nexus/REF_L_214746.nxs.h5"
REF_M_FILE = "/SNS/REF_M/IPTS-30794/nexus/REF_M_42112.nxs.h5"
VULCAN_FILE = "/SNS/VULCAN/IPTS-1234/nexus/VULCAN_12345.nxs.h5"
PG3_FILE = "/SNS/PG3/IPTS-4321/nexus/PG3_54321.nxs.h5"
NOM_FILE = "/SNS/NOM/IPTS-1001/nexus/NOM_10002.nxs.h5"

SCENARIOS = {
    # March-incident shape: a flood instrument (ARCS, stands in for CG2) sends
    # many runs first, then a victim (REF_L, stands in for EQSANS) sends a few.
    # On the shared FIFO queue the victim waits behind the entire flood.
    "blocking": [
        {
            "instrument": "arcs",
            "count": 60,
            "base": 880200,
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 8,
            "base": 870000,
            "facility": "SNS",
            "ipts": "IPTS-33077",
            "data_file": REF_L_FILE,
        },
    ],
    # One long "large dataset" run (VULCAN, ~20s via reduce_large.py) sent first,
    # then normal short runs from three other instruments. On a system with spare
    # workers the normals should not wait for the large job.
    "large-dataset": [
        {
            "instrument": "vulcan",
            "count": 1,
            "base": 300000,
            "facility": "SNS",
            "ipts": "IPTS-1234",
            "data_file": VULCAN_FILE,
        },
        {
            "instrument": "arcs",
            "count": 5,
            "base": 310000,
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 5,
            "base": 311000,
            "facility": "SNS",
            "ipts": "IPTS-33077",
            "data_file": REF_L_FILE,
        },
        {
            "instrument": "ref_m",
            "count": 5,
            "base": 312000,
            "facility": "SNS",
            "ipts": "IPTS-30794",
            "data_file": REF_M_FILE,
        },
    ],
    # Equal batches interleaved across five instruments. A fair system finishes
    # them roughly evenly; a shared FIFO serves them in submission order.
    "fairness": [
        {
            "instrument": "arcs",
            "count": 10,
            "base": 500000,
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 10,
            "base": 510000,
            "facility": "SNS",
            "ipts": "IPTS-33077",
            "data_file": REF_L_FILE,
        },
        {
            "instrument": "ref_m",
            "count": 10,
            "base": 520000,
            "facility": "SNS",
            "ipts": "IPTS-30794",
            "data_file": REF_M_FILE,
        },
        {
            "instrument": "pg3",
            "count": 10,
            "base": 530000,
            "facility": "SNS",
            "ipts": "IPTS-4321",
            "data_file": PG3_FILE,
        },
        {
            "instrument": "nom",
            "count": 10,
            "base": 540000,
            "facility": "SNS",
            "ipts": "IPTS-1001",
            "data_file": NOM_FILE,
        },
    ],
}


def db_now(db):
    """Read the current time from the database clock.

    Anchoring the window to the DB (not the host) avoids skew between the host
    running this script and the postgres container that stamps created_on.
    """
    import psycopg2

    params = dict(metrics.DEFAULT_DB)
    if db:
        params.update(db)
    conn = psycopg2.connect(**params)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT NOW();")
            return cur.fetchone()[0]
    finally:
        conn.close()


def send_workload(client, scenario, interleave):
    """Send the scenario's runs. Returns the set of (instrument, run_number)."""
    phases = SCENARIOS[scenario]
    sent = set()

    def _send(p, rn):
        client.send_run(
            p["instrument"],
            rn,
            facility=p.get("facility", "SNS"),
            data_file=p.get("data_file", "/SNS/EQSANS/data.nxs"),
            ipts=p.get("ipts", "IPTS-12345"),
        )
        sent.add((p["instrument"], rn))

    if interleave:
        # Round-robin one run per instrument per round (fairness scenario).
        max_count = max(p["count"] for p in phases)
        for i in range(max_count):
            for p in phases:
                if i < p["count"]:
                    _send(p, p["base"] + i)
    else:
        for p in phases:
            print(f"  phase: {p['instrument']} x{p['count']}")
            for i in range(p["count"]):
                _send(p, p["base"] + i)
    print(f"  sent {len(sent)} runs")
    return sent


def wait_for_drain(since, sent, db, timeout, poll_interval):
    """Poll the DB until every sent run has finished, or until timeout.

    Returns the final list of RunEvents (filtered to the sent runs).
    """
    deadline = time.time() + timeout
    while True:
        events = metrics.fetch_run_events(since, db)
        ours = [e for e in events if (e.instrument, e.run_number) in sent]
        finished = sum(1 for e in ours if e.finished is not None)
        print(f"  drain: {finished}/{len(sent)} finished ({len(ours)} seen) ...", flush=True)
        if finished >= len(sent):
            print("  all runs finished")
            return ours
        if time.time() >= deadline:
            print(f"  TIMEOUT after {timeout}s with {finished}/{len(sent)} finished")
            return ours
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scenario", choices=list(SCENARIOS), default="blocking")
    parser.add_argument("--host", default="localhost", help="ActiveMQ host")
    parser.add_argument("--port", type=int, default=61613, help="ActiveMQ STOMP port")
    parser.add_argument("--user", default="artemis", help="ActiveMQ user")
    parser.add_argument("--password", default="artemis", help="ActiveMQ password")
    parser.add_argument("--db-host", default="localhost", help="Postgres host")
    parser.add_argument("--db-port", type=int, default=5432, help="Postgres port")
    parser.add_argument("--capacity", type=int, default=10, help="worker slots = nodes * max_procs (default 2*5=10)")
    parser.add_argument("--timeout", type=int, default=300, help="max seconds to wait for drain")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--output", default="baseline_profile.json")
    parser.add_argument(
        "--analyze-only", action="store_true", help="skip sending; profile runs created in the last --since-minutes"
    )
    parser.add_argument("--since-minutes", type=float, default=10.0, help="window for --analyze-only mode")
    args = parser.parse_args()

    db = {"host": args.db_host, "port": args.db_port}

    if args.analyze_only:
        from datetime import timedelta

        since = db_now(db) - timedelta(minutes=args.since_minutes)
        events = metrics.fetch_run_events(since, db)
        report = metrics.build_report(events, capacity=args.capacity, window_start=since, window_end=db_now(db))
    else:
        window_start = db_now(db)
        print(f"window start (db clock): {window_start.isoformat()}")

        client = LoadTestClient(args.host, args.port, args.user, args.password)
        client.connect()
        try:
            print(f"sending scenario '{args.scenario}'...")
            sent = send_workload(client, args.scenario, interleave=(args.scenario == "fairness"))
        finally:
            client.disconnect()

        print("waiting for drain...")
        events = wait_for_drain(window_start, sent, db, args.timeout, args.poll_interval)
        report = metrics.build_report(events, capacity=args.capacity, window_start=window_start, window_end=db_now(db))

    print()
    print(metrics.render_text(report))

    with open(args.output, "w") as f:
        f.write(metrics.render_json(report))
    print(f"\nJSON report written to {args.output}")


if __name__ == "__main__":
    main()
