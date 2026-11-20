#!/usr/bin/env python
"""
Fake reduce_<INST>.py for load testing. Holds the worker for a while, then exits 0
so the run gets REDUCTION.COMPLETE.

Sleep time comes from the environment, which the agent passes through to the job:

    REDUCE_SLEEP_<INST>  seconds for one instrument, e.g. REDUCE_SLEEP_CG2=4
    REDUCE_SLEEP         seconds for the rest (default 1.5)

Keep it under the agent's task_time_limit_minutes or the job gets killed. Don't write
to stderr, the agent treats any stderr output as a failure.

To swap it in for a tests/data instrument in a running local stack:

    docker compose cp scripts/profiling/reduce_sleep.py \
      autoreducer:/SNS/ARCS/shared/autoreduce/reduce_ARCS.py
"""

import os
import sys
import time

DEFAULT_SLEEP_SECONDS = 1.5


def sleep_seconds(script_path, environ):
    """REDUCE_SLEEP_<INST>, then REDUCE_SLEEP, then the default."""
    name = os.path.splitext(os.path.basename(script_path))[0]
    instrument = name[len("reduce_") :] if name.startswith("reduce_") else name
    for key in (f"REDUCE_SLEEP_{instrument.upper()}", "REDUCE_SLEEP"):
        if key in environ:
            return float(environ[key])
    return DEFAULT_SLEEP_SECONDS


if __name__ == "__main__":
    seconds = sleep_seconds(sys.argv[0], os.environ)
    time.sleep(seconds)
    print(f"controlled-sleep reduction done in {seconds}s for", sys.argv[1:])
    sys.exit(0)
