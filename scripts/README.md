# scripts

Manual tooling for load testing and profiling the autoreduction queue. Nothing
here runs in CI, and nothing here is imported by the application. These are run
by hand against a local `docker compose` stack or the test env when investigating
throughput or queue fairness.

The unit tests are in `tests/test_profiling_metrics.py` and
`tests/test_load_test_instruments.py`.

The one exception: `Dockerfile.autoreducer` copies `load_test_instruments.py`
and `reduce_sleep.py` into the autoreducer image.

| Script | What it does |
| --- | --- |
| `profiling/metrics.py` | Reconstructs total time, per-instrument queue wait, and worker concurrency from the workflow database. Pure math is kept separate from database access so it can be tested directly. |
| `profiling/baseline_profile.py` | Sends a controlled workload, waits for the database to drain, then reports the metrics above. Scenarios: `blocking`, `large-dataset`, `fairness`, `each-instrument` (one run per load test instrument). Run numbers start from a new block every minute, so wait a minute before rerunning or pass an unused `--run-base`. |
| `profiling/reduce_sleep.py` | Stand-in for a real `reduce_<INST>.py`, holding a worker slot for a fixed time so a backlog can be built on demand. Sleep time comes from `REDUCE_SLEEP_<INST>`, then `REDUCE_SLEEP`, default 1.5 s. |
| `profiling/load_test_instruments.py` | The 21 extra SNS and HFIR load test instruments. Creates a placeholder data file and sleep script for each when the autoreducer image is built. |
| `load_test_per_instrument_queues.py` | Drives load through the queues for the first three scenarios, using the load test instruments. Also has the STOMP client `baseline_profile.py` sends with. |
| `investigate_artemis_fairness.py` | Measures whether an Artemis wildcard subscription delivers fairly across per-instrument queues. |
| `investigate_per_queue_fairness.py` | Measures whether Artemis alternates deliveries across separate per-queue subscriptions on one blocking consumer, for each prefetch header. |

Each script carries its own usage in its module docstring. Typical starting
point, with the stack already up:

```bash
docker compose up -d
docker compose stop webmonchow          # pause the noise generator
python scripts/profiling/baseline_profile.py --scenario blocking --capacity 1
```

Against the test env, with the passwords in `AMQ_PASSWORD` and `DATABASE_PASS`:

```bash
python scripts/profiling/baseline_profile.py --scenario each-instrument --capacity 3 \
    --host amqbroker-test.ornl.gov --user icat --db-host workflowdb-test.ornl.gov
```
