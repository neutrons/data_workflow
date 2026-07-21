#!/usr/bin/env python
"""
Controlled-time reduction fixture for load testing.

Drop-in replacement for a real ``reduce_<INST>.py`` inside the autoreducer
containers. It occupies a worker slot for a fixed duration and then exits 0, so
the run records a clean ``REDUCTION.COMPLETE``. This lets us control per-run
processing time precisely: only the *ratio* of arrival rate to processing time
matters for measuring contention, so a 1.5 s sleep is as valid as a 15 min
reduction (see METHODOLOGY.md, "Controlled processing time").

The sleep duration is read from the REDUCE_SLEEP environment variable (seconds),
defaulting to 1.5. For the "large dataset" instrument in the large-dataset
scenario, deploy a variant with a longer default (e.g. 20) instead.

Deploy into the running stack with:

    for svc in autoreducer autoreducer_himem; do
      for inst in ARCS REF_L REF_M PG3 NOM; do
        docker compose cp reduce_sleep.py \
          $svc:/SNS/$inst/shared/autoreduce/reduce_$inst.py
      done
    done
"""

import os
import sys
import time

SLEEP_SECONDS = float(os.environ.get("REDUCE_SLEEP", "1.5"))

time.sleep(SLEEP_SECONDS)
print("controlled-sleep reduction done for", sys.argv[1:])
sys.exit(0)
