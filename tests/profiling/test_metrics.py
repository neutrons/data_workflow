#!/usr/bin/env python3
"""
Unit tests for the profiling metric math.

These exercise the pure functions only (no database, no ActiveMQ), so they run
anywhere with::

    .pixi/envs/default/bin/python -m pytest tests/profiling/test_metrics.py
"""

import os
import sys
from datetime import datetime, timedelta

# tests/profiling is not on the pytest pythonpath, so make the sibling `metrics`
# module importable regardless of the pytest import mode (matches
# baseline_profile.py). Without this the import only works under the default
# "prepend" import mode.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from metrics import (  # noqa: E402
    RunEvent,
    build_report,
    compute_concurrency_timeline,
    compute_total_time,
    summarize_by_instrument,
    theoretical_min_seconds,
)

BASE = datetime(2026, 6, 29, 12, 0, 0)


def at(seconds):
    return BASE + timedelta(seconds=seconds)


def make_event(instrument, run, submit, start=None, complete=None):
    return RunEvent(
        instrument=instrument,
        run_number=run,
        submitted=at(submit),
        started=at(start) if start is not None else None,
        completed=at(complete) if complete is not None else None,
    )


def test_total_time_spans_first_submit_to_last_finish():
    events = [
        make_event("cg2", 1, submit=0, start=1, complete=5),
        make_event("eqsans", 2, submit=2, start=3, complete=10),
    ]
    assert compute_total_time(events) == 10.0  # 0 -> 10


def test_total_time_none_when_nothing_finished():
    events = [make_event("cg2", 1, submit=0, start=1)]
    assert compute_total_time(events) is None


def test_queue_wait_detects_blocking():
    # eqsans submitted early but not started until well after -> big wait
    blocked = make_event("eqsans", 1, submit=0, start=100, complete=101)
    assert blocked.queue_wait_seconds == 100.0


def test_per_instrument_breakdown_separates_waits():
    events = [
        # cg2 flood: starts almost immediately
        make_event("cg2", 1, submit=0, start=0, complete=2),
        make_event("cg2", 2, submit=0, start=0, complete=2),
        # eqsans: submitted at t=0 but blocked behind cg2 until t=50
        make_event("eqsans", 3, submit=0, start=50, complete=52),
    ]
    summaries = {s.instrument: s for s in summarize_by_instrument(events)}
    assert summaries["cg2"].max_queue_wait_seconds == 0.0
    assert summaries["eqsans"].max_queue_wait_seconds == 50.0
    assert summaries["cg2"].runs == 2
    assert summaries["eqsans"].completed == 1


def test_concurrency_counts_overlapping_intervals():
    events = [
        make_event("a", 1, submit=0, start=0, complete=10),
        make_event("b", 2, submit=0, start=2, complete=4),  # overlaps run 1
        make_event("c", 3, submit=0, start=20, complete=22),  # disjoint
    ]
    samples, max_conc, busy = compute_concurrency_timeline(events)
    assert max_conc == 2  # runs 1 and 2 overlap between t=2 and t=4
    assert busy == 10 + 2 + 2  # sum of interval durations


def test_concurrency_skips_incomplete_and_skewed():
    events = [
        make_event("a", 1, submit=0, start=0),  # never completed
        make_event("b", 2, submit=0, start=10, complete=5),  # negative -> skip
    ]
    samples, max_conc, busy = compute_concurrency_timeline(events)
    assert max_conc == 0
    assert busy == 0.0
    assert samples == []


def test_theoretical_min_divides_work_by_capacity():
    # 100 worker-seconds across 10 slots -> 10s floor
    assert theoretical_min_seconds(100.0, 10) == 10.0
    assert theoretical_min_seconds(100.0, 0) is None


def test_build_report_rolls_up_everything():
    events = [
        make_event("cg2", 1, submit=0, start=0, complete=6),
        make_event("eqsans", 2, submit=0, start=30, complete=36),
    ]
    report = build_report(events, capacity=10)
    assert report.total_runs == 2
    assert report.completed_runs == 2
    assert report.incomplete_runs == 0
    assert report.total_time_seconds == 36.0
    assert report.max_concurrency == 1  # the two runs never overlap
    assert report.busy_node_seconds == 12.0
    assert report.theoretical_min_seconds == 1.2
