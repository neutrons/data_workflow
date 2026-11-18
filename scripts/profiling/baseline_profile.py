#!/usr/bin/env python3
"""
Baseline profiling harness for the autoreduction queue.

This drives a controlled, reproducible workload through the *current* shared
queue (or the per-instrument queues, depending on configuration) and then
measures it with :mod:`metrics`. Unlike the older load-test script it does not
blindly ``sleep(30)`` - it waits for the work to actually drain by polling the
database, then reports the three metrics.

Run (with the stack up via ``docker compose up -d``)::

    python scripts/profiling/baseline_profile.py \\
        --scenario blocking --capacity 1

Against the test env, with passwords in AMQ_PASSWORD and DATABASE_PASS::

    python scripts/profiling/baseline_profile.py --scenario each-instrument --capacity 3 \\
        --host amqbroker-test.ornl.gov --user icat --db-host workflowdb-test.ornl.gov

Scenarios:
    blocking        - 60 ARCS runs flood, then 8 REF_L runs (shape of the March 2026 incident)
    large-dataset   - 1 VULCAN run ahead of normal runs from 3 instruments
    fairness        - 10 interleaved runs each from 5 instruments
    each-instrument - 1 run for each load test instrument, to check routing end to end

Run numbers count up from --run-base, which defaults to a new block every minute.
Two runs in the same minute get the same numbers and the second one's runs drop
out of the report, so wait a minute before rerunning or pass an unused --run-base.

Notes:
  * For a clean baseline, pause the noise generator first:
        docker compose stop webmonchow
  * "capacity" is how many of these runs can reduce at once: the nodes that run
    ReductionProcessor. Each node takes one job at a time, on STOMP too (the listener
    reads a job's output to the end before taking the next message, so max_procs
    doesn't add any). That's 1 locally, since autoreducer_himem only takes
    REDUCTION.HIMEM runs, and 3 on the test env.
"""

import argparse
import os
import sys
import time

# Reuse the STOMP sender from the sibling load-test module.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from load_test_per_instrument_queues import LoadTestClient  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import load_test_instruments  # noqa: E402
import metrics  # noqa: E402

# Each scenario is an ordered list of phases, sent in order, so the first phase
# builds the backlog. The data files must be ones baked into the autoreducer
# image (SNSdata.tar.gz): a run only occupies a worker if its file exists in the
# container, otherwise it errors out instantly and creates no contention.
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
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 8,
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
            "facility": "SNS",
            "ipts": "IPTS-1234",
            "data_file": VULCAN_FILE,
        },
        {
            "instrument": "arcs",
            "count": 5,
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 5,
            "facility": "SNS",
            "ipts": "IPTS-33077",
            "data_file": REF_L_FILE,
        },
        {
            "instrument": "ref_m",
            "count": 5,
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
            "facility": "SNS",
            "ipts": "IPTS-27800",
            "data_file": ARCS_FILE,
        },
        {
            "instrument": "ref_l",
            "count": 10,
            "facility": "SNS",
            "ipts": "IPTS-33077",
            "data_file": REF_L_FILE,
        },
        {
            "instrument": "ref_m",
            "count": 10,
            "facility": "SNS",
            "ipts": "IPTS-30794",
            "data_file": REF_M_FILE,
        },
        {
            "instrument": "pg3",
            "count": 10,
            "facility": "SNS",
            "ipts": "IPTS-4321",
            "data_file": PG3_FILE,
        },
        {
            "instrument": "nom",
            "count": 10,
            "facility": "SNS",
            "ipts": "IPTS-1001",
            "data_file": NOM_FILE,
        },
    ],
    # one run per load test instrument; the client fills in facility, IPTS and data file
    "each-instrument": [{"instrument": name, "count": 1} for name in sorted(load_test_instruments.INSTRUMENTS)],
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

    def _send(p):
        msg = client.send_run(
            p["instrument"],
            facility=p.get("facility"),
            data_file=p.get("data_file"),
            ipts=p.get("ipts"),
        )
        sent.add((p["instrument"], msg["run_number"]))

    if interleave:
        # Round-robin one run per instrument per round (fairness scenario).
        max_count = max(p["count"] for p in phases)
        for i in range(max_count):
            for p in phases:
                if i < p["count"]:
                    _send(p)
    else:
        for p in phases:
            print(f"  phase: {p['instrument']} x{p['count']}")
            for i in range(p["count"]):
                _send(p)
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
    parser.add_argument(
        "--password", default=os.environ.get("AMQ_PASSWORD", "artemis"), help="ActiveMQ password (env AMQ_PASSWORD)"
    )
    parser.add_argument("--db-host", default="localhost", help="Postgres host")
    parser.add_argument("--db-port", type=int, default=5432, help="Postgres port")
    parser.add_argument(
        "--db-password",
        default=os.environ.get("DATABASE_PASS", "workflow"),
        help="Postgres password (env DATABASE_PASS)",
    )
    parser.add_argument("--run-base", type=int, help="first run number (default: unique per minute)")
    parser.add_argument("--capacity", type=int, default=1, help="runs that can reduce at once (see Notes)")
    parser.add_argument("--timeout", type=int, default=300, help="max seconds to wait for drain")
    parser.add_argument("--poll-interval", type=float, default=2.0)
    parser.add_argument("--output", default="baseline_profile.json")
    parser.add_argument(
        "--analyze-only", action="store_true", help="skip sending; profile runs created in the last --since-minutes"
    )
    parser.add_argument("--since-minutes", type=float, default=10.0, help="window for --analyze-only mode")
    args = parser.parse_args()

    db = {"host": args.db_host, "port": args.db_port, "password": args.db_password}

    if args.analyze_only:
        from datetime import timedelta

        since = db_now(db) - timedelta(minutes=args.since_minutes)
        events = metrics.fetch_run_events(since, db)
        report = metrics.build_report(events, capacity=args.capacity, window_start=since, window_end=db_now(db))
    else:
        window_start = db_now(db)
        print(f"window start (db clock): {window_start.isoformat()}")

        client = LoadTestClient(args.host, args.port, args.user, args.password, run_base=args.run_base)
        print(f"run numbers start at {client.run_base}")
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
