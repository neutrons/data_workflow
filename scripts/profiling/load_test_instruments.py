#!/usr/bin/env python3
"""
Fake instruments for load testing the per-instrument reduction queues.

Each one gets an empty data file and a copy of reduce_sleep.py as its reduce script,
so a flood of runs holds real worker slots. Dockerfile.autoreducer runs this at build
time, and the load test scripts import INSTRUMENTS and data_file() from here.

The tests/data instruments are left out on purpose, since the system tests use their
real reduce scripts.

All runs of an instrument point at the same data file. The agent names its reduction
log after the data file, so concurrent runs share a log, which is fine here because
the sleep script never writes to stderr.

Runs on the autoreducer's system Python 3.9, so stdlib only.

    python3 load_test_instruments.py --root / --script /opt/load_test/reduce_sleep.py
"""

import argparse
import os
import shutil
import sys
from typing import NamedTuple


class FakeInstrument(NamedTuple):
    facility: str
    ipts: str


# real instrument names so routing and WebMon look like prod
INSTRUMENTS = {
    # SNS
    "bss": FakeInstrument("SNS", "IPTS-90001"),
    "corelli": FakeInstrument("SNS", "IPTS-90002"),
    "eqsans": FakeInstrument("SNS", "IPTS-90003"),
    "hys": FakeInstrument("SNS", "IPTS-90004"),
    "mandi": FakeInstrument("SNS", "IPTS-90005"),
    "seq": FakeInstrument("SNS", "IPTS-90006"),
    "snap": FakeInstrument("SNS", "IPTS-90007"),
    "topaz": FakeInstrument("SNS", "IPTS-90008"),
    "usans": FakeInstrument("SNS", "IPTS-90009"),
    "venus": FakeInstrument("SNS", "IPTS-90010"),
    "vis": FakeInstrument("SNS", "IPTS-90011"),
    # HFIR
    "cg1d": FakeInstrument("HFIR", "IPTS-90101"),
    "cg2": FakeInstrument("HFIR", "IPTS-90102"),
    "cg3": FakeInstrument("HFIR", "IPTS-90103"),
    "hb1": FakeInstrument("HFIR", "IPTS-90104"),
    "hb1a": FakeInstrument("HFIR", "IPTS-90105"),
    "hb2a": FakeInstrument("HFIR", "IPTS-90106"),
    "hb2b": FakeInstrument("HFIR", "IPTS-90107"),
    "hb2c": FakeInstrument("HFIR", "IPTS-90108"),
    "hb3": FakeInstrument("HFIR", "IPTS-90109"),
    "hb3a": FakeInstrument("HFIR", "IPTS-90110"),
}

# only names the data file; the load tests send their own run numbers
PLACEHOLDER_RUN = 1


def data_file(instrument, root="/"):
    """Data file path to put in the run messages."""
    inst = INSTRUMENTS[instrument]
    name = instrument.upper()
    return os.path.join(root, inst.facility, name, inst.ipts, "nexus", f"{name}_{PLACEHOLDER_RUN}.nxs.h5")


def reduce_script(instrument, root="/"):
    """Where the agent looks for the reduce script."""
    inst = INSTRUMENTS[instrument]
    name = instrument.upper()
    return os.path.join(root, inst.facility, name, "shared", "autoreduce", f"reduce_{name}.py")


def create_tree(root, script):
    """Create the data file and reduce script for each instrument. Existing scripts are left alone."""
    created = []
    for instrument in sorted(INSTRUMENTS):
        target = reduce_script(instrument, root)
        if os.path.exists(target):
            print(f"skipping {instrument}: {target} already exists")
            continue
        placeholder = data_file(instrument, root)
        os.makedirs(os.path.dirname(placeholder), exist_ok=True)
        open(placeholder, "a").close()
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copyfile(script, target)
        created.append(instrument)
    print(f"created {len(created)} load test instruments under {root}")
    return created


def main(argv=None):
    parser = argparse.ArgumentParser(description="Create the fake load test instruments.")
    parser.add_argument("--root", default="/", help="directory to create /SNS and /HFIR under")
    parser.add_argument(
        "--script",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "reduce_sleep.py"),
        help="sleep script to install as each reduce_<INST>.py",
    )
    args = parser.parse_args(argv)
    if not os.path.isfile(args.script):
        print(f"sleep script not found: {args.script}", file=sys.stderr)
        return 1
    create_tree(args.root, args.script)
    return 0


if __name__ == "__main__":
    sys.exit(main())
