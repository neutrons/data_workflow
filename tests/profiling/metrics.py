#!/usr/bin/env python3
"""
Profiling metrics for autoreduction queue load tests.

This module turns the run-status history recorded in the workflow database into
the three metrics we care about when comparing queue architectures (shared
first-in-first-out queue vs. per-instrument queues):

  1. Total time   - first run submitted -> last run finished (overall throughput)
  2. Per instrument - the same span, broken down per instrument. A blocked
                      instrument shows up as a large gap between its first
                      submit and its first REDUCTION.STARTED.
  3. Worker concurrency over time - how many reductions are running at once,
                      derived by overlapping each run's
                      [REDUCTION.STARTED, REDUCTION.COMPLETE] interval. This is
                      our proxy for "how many worker slots are busy vs idle".

Everything is derived from the database alone, so the exact same analysis works
for the baseline (shared queue) and the per-instrument runs - the status queue
names (REDUCTION.STARTED / REDUCTION.COMPLETE) are independent of how messages
were routed to the workers.

The math lives in pure functions (no DB) so it can be unit tested directly.
Database access is isolated to ``fetch_run_events`` and imports psycopg2 lazily.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Optional

# Status-queue name prefixes recorded by the autoreducer as a run is processed.
# These match the values in the post_process_consumer.conf and are the same
# regardless of per-instrument routing.
STARTED_PREFIX = "REDUCTION.STARTED"
COMPLETE_PREFIX = "REDUCTION.COMPLETE"
ERROR_PREFIX = "REDUCTION.ERROR"


@dataclass
class RunEvent:
    """One data run and the timestamps of its journey through reduction."""

    instrument: str
    run_number: int
    submitted: datetime  # report_datarun.created_on (entered the system)
    started: Optional[datetime] = None  # first REDUCTION.STARTED
    completed: Optional[datetime] = None  # first REDUCTION.COMPLETE
    errored: Optional[datetime] = None  # first REDUCTION.ERROR

    @property
    def finished(self) -> Optional[datetime]:
        """When the run left the workers (completed or errored, whichever first)."""
        candidates = [t for t in (self.completed, self.errored) if t is not None]
        return min(candidates) if candidates else None

    @property
    def queue_wait_seconds(self) -> Optional[float]:
        """Seconds spent waiting between submission and a worker picking it up.

        This is the headline blocking signal: a flooded shared queue inflates
        this for the instruments stuck behind the flood.
        """
        if self.started is None:
            return None
        return (self.started - self.submitted).total_seconds()

    @property
    def processing_seconds(self) -> Optional[float]:
        """Seconds a worker slot was held by this run."""
        if self.started is None or self.finished is None:
            return None
        return (self.finished - self.started).total_seconds()


@dataclass
class InstrumentSummary:
    instrument: str
    runs: int
    completed: int
    first_submit: datetime
    last_finish: Optional[datetime]
    total_span_seconds: Optional[float]
    avg_queue_wait_seconds: Optional[float]
    max_queue_wait_seconds: Optional[float]
    avg_processing_seconds: Optional[float]


@dataclass
class ConcurrencySample:
    t: datetime
    active: int


@dataclass
class ProfileReport:
    window_start: Optional[datetime]
    window_end: Optional[datetime]
    total_runs: int
    completed_runs: int
    incomplete_runs: int
    total_time_seconds: Optional[float]
    per_instrument: list = field(default_factory=list)
    max_concurrency: int = 0
    capacity: Optional[int] = None
    busy_node_seconds: float = 0.0
    theoretical_min_seconds: Optional[float] = None
    timeline: list = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Pure analysis functions (no database, directly unit-testable)
# --------------------------------------------------------------------------- #
def compute_total_time(events: list) -> Optional[float]:
    """Wall-clock seconds from the earliest submission to the latest finish.

    Returns None if nothing finished yet.
    """
    submits = [e.submitted for e in events]
    finishes = [e.finished for e in events if e.finished is not None]
    if not submits or not finishes:
        return None
    return (max(finishes) - min(submits)).total_seconds()


def summarize_by_instrument(events: list) -> list:
    """Per-instrument breakdown, sorted by instrument name.

    The interesting comparison between architectures is the spread of
    ``max_queue_wait_seconds`` across instruments: under a fair system every
    instrument's worst wait should be similar; under the shared queue the
    instrument that floods has a small wait while everyone else's balloons.
    """
    by_inst: dict = {}
    for e in events:
        by_inst.setdefault(e.instrument, []).append(e)

    summaries = []
    for instrument in sorted(by_inst):
        group = by_inst[instrument]
        finishes = [e.finished for e in group if e.finished is not None]
        waits = [e.queue_wait_seconds for e in group if e.queue_wait_seconds is not None]
        procs = [e.processing_seconds for e in group if e.processing_seconds is not None]
        first_submit = min(e.submitted for e in group)
        last_finish = max(finishes) if finishes else None
        summaries.append(
            InstrumentSummary(
                instrument=instrument,
                runs=len(group),
                completed=len(finishes),
                first_submit=first_submit,
                last_finish=last_finish,
                total_span_seconds=((last_finish - first_submit).total_seconds() if last_finish else None),
                avg_queue_wait_seconds=(sum(waits) / len(waits) if waits else None),
                max_queue_wait_seconds=(max(waits) if waits else None),
                avg_processing_seconds=(sum(procs) / len(procs) if procs else None),
            )
        )
    return summaries


def compute_concurrency_timeline(events: list):
    """Sweep the [started, finished] intervals to find concurrent worker usage.

    Returns ``(samples, max_concurrency, busy_node_seconds)`` where ``samples``
    is a list of :class:`ConcurrencySample` marking every point the active count
    changes. ``busy_node_seconds`` is the integral of the active count over time
    i.e. the total worker-slot-seconds consumed.
    """
    deltas: dict = {}
    busy_node_seconds = 0.0
    for e in events:
        if e.started is None or e.finished is None:
            continue
        if e.finished < e.started:
            # Clock skew / bad data - skip rather than produce negative time.
            continue
        deltas[e.started] = deltas.get(e.started, 0) + 1
        deltas[e.finished] = deltas.get(e.finished, 0) - 1
        busy_node_seconds += (e.finished - e.started).total_seconds()

    samples = []
    active = 0
    max_concurrency = 0
    for t in sorted(deltas):
        active += deltas[t]
        max_concurrency = max(max_concurrency, active)
        samples.append(ConcurrencySample(t=t, active=active))
    return samples, max_concurrency, busy_node_seconds


def theoretical_min_seconds(busy_node_seconds: float, capacity: int) -> Optional[float]:
    """Fastest possible wall-clock: total work divided by worker capacity.

    capacity = number of autoreducer nodes * max_procs per node. This is the
    floor Pete described - we can never beat sum(processing_time) / nodes.
    """
    if not capacity:
        return None
    return busy_node_seconds / capacity


def build_report(
    events: list,
    capacity: Optional[int] = None,
    window_start: Optional[datetime] = None,
    window_end: Optional[datetime] = None,
) -> ProfileReport:
    """Assemble the full :class:`ProfileReport` from a list of run events."""
    completed = [e for e in events if e.finished is not None]
    samples, max_conc, busy = compute_concurrency_timeline(events)
    return ProfileReport(
        window_start=window_start,
        window_end=window_end,
        total_runs=len(events),
        completed_runs=len(completed),
        incomplete_runs=len(events) - len(completed),
        total_time_seconds=compute_total_time(events),
        per_instrument=summarize_by_instrument(events),
        max_concurrency=max_conc,
        capacity=capacity,
        busy_node_seconds=busy,
        theoretical_min_seconds=(theoretical_min_seconds(busy, capacity) if capacity else None),
        timeline=samples,
    )


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def _fmt(seconds: Optional[float]) -> str:
    return f"{seconds:.1f}s" if seconds is not None else "n/a"


def render_text(report: ProfileReport) -> str:
    """Human-readable report for the terminal / log."""
    lines = []
    lines.append("=" * 70)
    lines.append("AUTOREDUCTION PROFILE")
    lines.append("=" * 70)
    if report.window_start:
        lines.append(f"Window start : {report.window_start.isoformat()}")
    if report.window_end:
        lines.append(f"Window end   : {report.window_end.isoformat()}")
    lines.append(
        f"Runs         : {report.total_runs} ({report.completed_runs} finished, {report.incomplete_runs} incomplete)"
    )
    lines.append("")
    lines.append("METRIC 1 - Total time (first submit -> last finish)")
    lines.append(f"  {_fmt(report.total_time_seconds)}")
    if report.theoretical_min_seconds is not None:
        eff = ""
        if report.total_time_seconds:
            eff = f"  (efficiency {report.theoretical_min_seconds / report.total_time_seconds * 100:.0f}%)"
        lines.append(f"  theoretical min @ capacity {report.capacity}: {_fmt(report.theoretical_min_seconds)}{eff}")
    lines.append("")
    lines.append("METRIC 2 - Per instrument (watch max-wait spread for blocking)")
    header = f"  {'instrument':<12}{'runs':>5}{'done':>5}{'span':>10}{'avg wait':>10}{'max wait':>10}{'avg proc':>10}"
    lines.append(header)
    for s in report.per_instrument:
        lines.append(
            f"  {s.instrument:<12}{s.runs:>5}{s.completed:>5}"
            f"{_fmt(s.total_span_seconds):>10}{_fmt(s.avg_queue_wait_seconds):>10}"
            f"{_fmt(s.max_queue_wait_seconds):>10}{_fmt(s.avg_processing_seconds):>10}"
        )
    lines.append("")
    lines.append("METRIC 3 - Worker concurrency")
    cap = f" of {report.capacity}" if report.capacity else ""
    lines.append(f"  peak concurrent reductions: {report.max_concurrency}{cap}")
    lines.append(f"  busy worker-seconds total : {_fmt(report.busy_node_seconds)}")
    lines.append("=" * 70)
    return "\n".join(lines)


def to_dict(report: ProfileReport) -> dict:
    """JSON-serializable dict (datetimes -> ISO strings)."""

    def convert(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    return convert(asdict(report))


def render_json(report: ProfileReport) -> str:
    return json.dumps(to_dict(report), indent=2)


# --------------------------------------------------------------------------- #
# Database access (psycopg2 imported lazily so the math above stays importable)
# --------------------------------------------------------------------------- #
DEFAULT_DB = {
    "host": "localhost",
    "port": 5432,
    "dbname": "workflow",
    "user": "workflow",
    "password": "workflow",
}

# NOTE on column names: these models use ForeignKey fields literally named
# ``run_id`` and ``queue_id``, so Django's generated DB columns are
# ``run_id_id`` and ``queue_id_id``. (The shorthand SQL in the old load-test
# script joined on ``run_id``/``queue_id`` and would have errored.)
_FETCH_SQL = """
SELECT
    inst.name        AS instrument,
    dr.run_number    AS run_number,
    dr.created_on    AS submitted,
    MIN(CASE WHEN sq.name LIKE %(started)s THEN rs.created_on END)  AS started,
    MIN(CASE WHEN sq.name LIKE %(complete)s THEN rs.created_on END) AS completed,
    MIN(CASE WHEN sq.name LIKE %(error)s THEN rs.created_on END)    AS errored
FROM report_datarun dr
JOIN report_instrument inst ON dr.instrument_id_id = inst.id
LEFT JOIN report_runstatus rs ON rs.run_id_id = dr.id
LEFT JOIN report_statusqueue sq ON rs.queue_id_id = sq.id
WHERE dr.created_on >= %(since)s
GROUP BY inst.name, dr.run_number, dr.created_on
ORDER BY dr.created_on;
"""


def fetch_run_events(since: datetime, db: Optional[dict] = None) -> list:
    """Query the workflow DB for run events created at/after ``since``.

    Returns a list of :class:`RunEvent`. Requires psycopg2 and a reachable
    database (the ``db`` service exposes port 5432 on localhost in
    docker-compose).
    """
    import psycopg2  # local import: keeps the pure math usable without a DB

    params = dict(DEFAULT_DB)
    if db:
        params.update(db)

    conn = psycopg2.connect(**params)
    try:
        with conn.cursor() as cur:
            cur.execute(
                _FETCH_SQL,
                {
                    "started": STARTED_PREFIX + "%",
                    "complete": COMPLETE_PREFIX + "%",
                    "error": ERROR_PREFIX + "%",
                    "since": since,
                },
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    events = []
    for instrument, run_number, submitted, started, completed, errored in rows:
        events.append(
            RunEvent(
                instrument=instrument,
                run_number=run_number,
                submitted=submitted,
                started=started,
                completed=completed,
                errored=errored,
            )
        )
    return events
