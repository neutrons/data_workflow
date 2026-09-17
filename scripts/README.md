# scripts

Manual tooling for load testing and profiling the autoreduction queue. Nothing
here runs in CI, and nothing here is imported by the application. These are run
by hand against a local `docker compose` stack when investigating throughput or
queue fairness.

The unit tests for the profiling math live with the rest of the tests, in
`tests/test_profiling_metrics.py`.

| Script | What it does |
| --- | --- |
| `profiling/metrics.py` | Reconstructs total time, per-instrument queue wait, and worker concurrency from the workflow database. Pure math is kept separate from database access so it can be tested directly. |
| `profiling/baseline_profile.py` | Sends a controlled workload, waits for the database to drain, then reports the metrics above. Scenarios: `blocking`, `large-dataset`, `fairness`. |
| `profiling/reduce_sleep.py` | Stand-in for a real `reduce_<INST>.py`, holding a worker slot for a fixed time so a backlog can be built on demand. |
| `load_test_per_instrument_queues.py` | Drives load through the queues for the same three scenarios. |
| `investigate_artemis_fairness.py` | Measures whether an Artemis wildcard subscription delivers fairly across per-instrument queues. |

Each script carries its own usage in its module docstring. Typical starting
point, with the stack already up:

```bash
docker compose up -d
docker compose stop webmonchow          # pause the noise generator
python scripts/profiling/baseline_profile.py --scenario blocking --capacity 10
```
