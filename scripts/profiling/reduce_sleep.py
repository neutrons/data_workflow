#!/usr/bin/env python
"""
Controlled-time reduction fixture for load testing.

Drop-in replacement for a real ``reduce_<INST>.py`` inside the autoreducer
containers. It holds a worker slot for REDUCE_SLEEP seconds (default 1.5) then
exits 0, so the run records a clean ``REDUCTION.COMPLETE``. Only the ratio of
arrival rate to processing time matters for measuring contention, so a short
sleep stands in for a long reduction.

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
