#!/usr/bin/env python3
"""
Load test for per-instrument queue isolation.

Simulates the March 10-11, 2026 incident where high-volume instruments
blocked processing for other instruments.

Usage:
    # Start services
    docker-compose up -d artemis postgres webmonchow

    # Run load test
    python3 tests/load_test_per_instrument_queues.py --scenario blocking

    # Check results
    python3 tests/load_test_per_instrument_queues.py --analyze results.json
"""

import argparse
import json
import sys
import time
from collections import defaultdict
from datetime import datetime

import stomp


class LoadTestClient:
    """Client for sending test messages to ActiveMQ."""

    def __init__(self, host="localhost", port=61613, user="admin", password="admin"):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.conn = None

    def connect(self):
        """Connect to ActiveMQ broker."""
        self.conn = stomp.Connection([(self.host, self.port)])
        self.conn.connect(self.user, self.password, wait=True)
        print(f"✓ Connected to ActiveMQ at {self.host}:{self.port}")

    def disconnect(self):
        """Disconnect from broker."""
        if self.conn and self.conn.is_connected():
            self.conn.disconnect()

    def send_run(self, instrument, run_number, data_file="/SNS/EQSANS/data.nxs", facility="SNS", ipts="IPTS-12345"):
        """Send a single run message."""
        message = {
            "instrument": instrument,
            "run_number": run_number,
            "data_file": data_file,
            "facility": facility,
            "ipts": ipts,
            "timestamp": datetime.now().isoformat(),
        }

        self.conn.send(
            destination="/queue/POSTPROCESS.DATA_READY", body=json.dumps(message), headers={"persistent": "true"}
        )

        return message


class LoadTestScenario:
    """Base class for load test scenarios."""

    def __init__(self, client):
        self.client = client
        self.messages_sent = []
        self.start_time = None
        self.end_time = None

    def run(self):
        """Execute the scenario."""
        raise NotImplementedError

    def get_stats(self):
        """Get scenario statistics."""
        duration = (self.end_time - self.start_time) if self.end_time else 0

        by_instrument = defaultdict(int)
        for msg in self.messages_sent:
            by_instrument[msg["instrument"]] += 1

        return {
            "total_messages": len(self.messages_sent),
            "duration_seconds": duration,
            "messages_per_second": len(self.messages_sent) / duration if duration > 0 else 0,
            "by_instrument": dict(by_instrument),
            "start_time": self.start_time,
            "end_time": self.end_time,
        }


class BlockingScenario(LoadTestScenario):
    """
    Simulates March 10-11 incident: High-volume instrument floods queue.

    Expected behavior WITH per-instrument queues:
    - EQSANS messages process immediately despite CG2 backlog
    - Both instruments make steady progress

    Expected behavior WITHOUT per-instrument queues (shared queue):
    - EQSANS waits for all CG2 messages to clear
    - EQSANS experiences significant delay
    """

    def run(self):
        """Run blocking scenario."""
        print("\n" + "=" * 70)
        print("SCENARIO: High-Volume Instrument Blocking")
        print("=" * 70)
        print("Simulating CG2 flooding queue with 200 runs")
        print("While EQSANS tries to process 10 runs")
        print()

        self.start_time = time.time()

        # Phase 1: CG2 floods the queue (represents backlog)
        print("Phase 1: CG2 sends 200 runs (creating backlog)...")
        for i in range(200):
            msg = self.client.send_run("cg2", 10000 + i, facility="HFIR")
            self.messages_sent.append(msg)

            if (i + 1) % 50 == 0:
                print(f"  Sent {i + 1}/200 CG2 runs")

        print("✓ CG2 backlog created\n")

        # Phase 2: EQSANS tries to process (should NOT be blocked)
        print("Phase 2: EQSANS sends 10 runs (should process immediately)...")

        for i in range(10):
            msg = self.client.send_run("eqsans", 20000 + i, facility="SNS")
            msg["eqsans_send_time"] = time.time()
            self.messages_sent.append(msg)

        print(f"✓ EQSANS runs sent at t={time.time() - self.start_time:.1f}s\n")

        # Phase 3: Monitor processing
        print("Phase 3: Monitoring (30 seconds)...")
        print("  Check database to see if EQSANS runs complete despite CG2 backlog")
        print("  With per-instrument queues: EQSANS should complete in <5s")
        print("  Without per-instrument queues: EQSANS waits for CG2 to clear")

        time.sleep(30)

        self.end_time = time.time()

        return self.get_stats()


class LargeDatasetScenario(LoadTestScenario):
    """
    Simulates VENUS large dataset blocking workers.

    Tests that one large run doesn't prevent other instruments from processing.
    """

    def run(self):
        """Run large dataset scenario."""
        print("\n" + "=" * 70)
        print("SCENARIO: Large Dataset Worker Monopolization")
        print("=" * 70)
        print("Simulating VENUS sending large run (1000+ files, 60+ min)")
        print("While other instruments send normal runs")
        print()

        self.start_time = time.time()

        # Phase 1: VENUS sends large dataset
        print("Phase 1: VENUS sends large dataset run...")
        msg = self.client.send_run(
            "venus",
            30000,
            facility="SNS",
            data_file="/SNS/VENUS/large_dataset_1000_files.nxs",  # Marker for large dataset
        )
        msg["large_dataset"] = True
        self.messages_sent.append(msg)
        print("✓ VENUS large dataset queued\n")

        # Phase 2: Other instruments send normal runs
        print("Phase 2: Other instruments send normal runs...")
        normal_instruments = ["eqsans", "hb2c", "cg3"]

        for inst in normal_instruments:
            for i in range(5):
                msg = self.client.send_run(inst, 40000 + i)
                self.messages_sent.append(msg)
            print(f"  ✓ {inst.upper()}: 5 runs sent")

        print("\nWith per-instrument queues: Normal runs should NOT wait for VENUS")
        print("Without per-instrument queues: Normal runs blocked behind VENUS\n")

        # Monitor
        print("Monitoring for 30 seconds...")
        time.sleep(30)

        self.end_time = time.time()

        return self.get_stats()


class FairnessScenario(LoadTestScenario):
    """
    Tests fair distribution of processing across instruments.

    All instruments should make similar progress, not FIFO order bias.
    """

    def run(self):
        """Run fairness scenario."""
        print("\n" + "=" * 70)
        print("SCENARIO: Fairness Test")
        print("=" * 70)
        print("Sending 20 runs each for 5 instruments")
        print("Measuring processing fairness")
        print()

        self.start_time = time.time()

        instruments = ["eqsans", "venus", "cg2", "hb2c", "nomad"]

        # Interleave messages from all instruments
        for i in range(20):
            for inst in instruments:
                msg = self.client.send_run(inst, 50000 + i * len(instruments) + instruments.index(inst))
                msg["batch"] = i
                self.messages_sent.append(msg)

            if (i + 1) % 5 == 0:
                print(f"  Sent batch {i + 1}/20 (5 instruments × {i + 1} runs)")

        print("\n✓ All messages sent")
        print("\nWith per-instrument queues: All instruments should process ~evenly")
        print("Without per-instrument queues: FIFO order creates uneven distribution\n")

        # Monitor
        print("Monitoring for 60 seconds...")
        time.sleep(60)

        self.end_time = time.time()

        return self.get_stats()


def analyze_results(results_file):
    """Analyze load test results from database."""
    print("\n" + "=" * 70)
    print("ANALYZING RESULTS")
    print("=" * 70)
    print("Query database to check processing times and fairness\n")

    # This would query the database to analyze:
    # 1. Time from message sent to processing complete
    # 2. Per-instrument throughput
    # 3. Fairness metrics (coefficient of variation)
    # 4. Detection of blocking incidents

    print("SQL queries to run:")
    print()
    print("-- Check EQSANS processing times during CG2 backlog")
    print("""
    SELECT
        instrument_id.name,
        r.run_number,
        r.created_on,
        s.created_on as completed_on,
        EXTRACT(EPOCH FROM (s.created_on - r.created_on)) as processing_seconds
    FROM report_datarun r
    JOIN report_instrument instrument_id ON r.instrument_id = instrument_id.id
    JOIN report_runstatus s ON r.run_status_id = s.id
    WHERE r.created_on > NOW() - INTERVAL '5 minutes'
    ORDER BY r.created_on;
    """)

    print("\n-- Calculate per-instrument processing rates")
    print("""
    SELECT
        instrument_id.name,
        COUNT(*) as runs_processed,
        AVG(EXTRACT(EPOCH FROM (s.created_on - r.created_on))) as avg_seconds
    FROM report_datarun r
    JOIN report_instrument instrument_id ON r.instrument_id = instrument_id.id
    JOIN report_runstatus s ON r.run_status_id = s.id
    WHERE r.created_on > NOW() - INTERVAL '5 minutes'
    GROUP BY instrument_id.name
    ORDER BY runs_processed DESC;
    """)

    print("\n-- Check for blocked instruments (long wait times)")
    print("""
    SELECT
        instrument_id.name,
        r.run_number,
        EXTRACT(EPOCH FROM (s.created_on - r.created_on)) as wait_seconds
    FROM report_datarun r
    JOIN report_instrument instrument_id ON r.instrument_id = instrument_id.id
    JOIN report_runstatus s ON r.run_status_id = s.id
    WHERE r.created_on > NOW() - INTERVAL '5 minutes'
      AND EXTRACT(EPOCH FROM (s.created_on - r.created_on)) > 300  -- > 5 min wait
    ORDER BY wait_seconds DESC;
    """)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Load test per-instrument queue isolation")
    parser.add_argument(
        "--scenario",
        choices=["blocking", "large-dataset", "fairness", "all"],
        default="all",
        help="Test scenario to run",
    )
    parser.add_argument("--host", default="localhost", help="ActiveMQ host")
    parser.add_argument("--port", type=int, default=61613, help="ActiveMQ STOMP port")
    parser.add_argument("--user", default="admin", help="ActiveMQ user")
    parser.add_argument("--password", default="admin", help="ActiveMQ password")
    parser.add_argument("--analyze", help="Analyze results from JSON file")
    parser.add_argument("--output", default="load_test_results.json", help="Output file for results")

    args = parser.parse_args()

    if args.analyze:
        analyze_results(args.analyze)
        return

    # Connect to ActiveMQ
    client = LoadTestClient(args.host, args.port, args.user, args.password)

    try:
        client.connect()

        scenarios = {"blocking": BlockingScenario, "large-dataset": LargeDatasetScenario, "fairness": FairnessScenario}

        # Determine which scenarios to run
        if args.scenario == "all":
            to_run = scenarios.keys()
        else:
            to_run = [args.scenario]

        # Run scenarios
        all_results = {}

        for scenario_name in to_run:
            scenario_class = scenarios[scenario_name]
            scenario = scenario_class(client)

            print(f"\nExecuting: {scenario_name}")
            results = scenario.run()
            all_results[scenario_name] = results

            print("\n" + "-" * 70)
            print("SCENARIO STATS:")
            print(json.dumps(results, indent=2, default=str))
            print("-" * 70)

            # Pause between scenarios
            if scenario_name != list(to_run)[-1]:
                print("\nWaiting 10 seconds before next scenario...")
                time.sleep(10)

        # Save results
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2, default=str)

        print(f"\n✓ Results saved to {args.output}")
        print(f"\nRun analysis: python3 {sys.argv[0]} --analyze {args.output}")

    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
