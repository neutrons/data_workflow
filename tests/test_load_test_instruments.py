"""Tests for the load test tooling in scripts/: fake instruments, sleep script, run numbers. Doesn't need the stack."""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

import pytest

# scripts/ isn't on the pytest pythonpath
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROFILING_DIR = os.path.join(_REPO_ROOT, "scripts", "profiling")
sys.path.insert(0, _PROFILING_DIR)
sys.path.insert(0, os.path.join(_REPO_ROOT, "scripts"))

import baseline_profile  # noqa: E402
import load_test_instruments as lti  # noqa: E402
from load_test_per_instrument_queues import LoadTestClient, default_run_base  # noqa: E402
from reduce_sleep import DEFAULT_SLEEP_SECONDS, sleep_seconds  # noqa: E402

SLEEP_SCRIPT = os.path.join(_PROFILING_DIR, "reduce_sleep.py")


class TestInstrumentList:
    def test_does_not_replace_system_test_instruments(self):
        # the system tests use the real reduce scripts in tests/data
        existing = set(os.listdir(os.path.join(_REPO_ROOT, "tests", "data")))
        assert not existing & {name.upper() for name in lti.INSTRUMENTS}

    def test_names_are_routable(self):
        # same check the workflow manager does before routing
        for name in lti.INSTRUMENTS:
            assert re.match(r"^[a-z0-9_]+$", name), name

    def test_about_thirty_with_tests_data(self):
        existing = os.listdir(os.path.join(_REPO_ROOT, "tests", "data"))
        assert len(lti.INSTRUMENTS) + len(existing) >= 28

    def test_covers_both_facilities(self):
        assert {inst.facility for inst in lti.INSTRUMENTS.values()} == {"SNS", "HFIR"}

    def test_paths_match_what_the_agent_expects(self):
        assert lti.data_file("cg2") == "/HFIR/CG2/IPTS-90102/nexus/CG2_1.nxs.h5"
        assert lti.reduce_script("cg2") == "/HFIR/CG2/shared/autoreduce/reduce_CG2.py"


class TestCreateTree:
    def test_creates_placeholder_and_script_for_every_instrument(self, tmp_path):
        created = lti.create_tree(str(tmp_path), SLEEP_SCRIPT)

        assert sorted(created) == sorted(lti.INSTRUMENTS)
        with open(SLEEP_SCRIPT) as f:
            expected = f.read()
        for name in lti.INSTRUMENTS:
            placeholder = lti.data_file(name, str(tmp_path))
            assert os.path.isfile(placeholder)
            assert os.path.getsize(placeholder) == 0
            with open(lti.reduce_script(name, str(tmp_path))) as f:
                assert f.read() == expected

    def test_leaves_an_existing_script_alone(self, tmp_path):
        target = lti.reduce_script("eqsans", str(tmp_path))
        os.makedirs(os.path.dirname(target))
        with open(target, "w") as f:
            f.write("# real script\n")

        created = lti.create_tree(str(tmp_path), SLEEP_SCRIPT)

        assert "eqsans" not in created
        with open(target) as f:
            assert f.read() == "# real script\n"

    def test_is_safe_to_rerun(self, tmp_path):
        lti.create_tree(str(tmp_path), SLEEP_SCRIPT)
        assert lti.create_tree(str(tmp_path), SLEEP_SCRIPT) == []

    def test_main_fails_without_the_sleep_script(self, tmp_path):
        assert lti.main(["--root", str(tmp_path), "--script", str(tmp_path / "missing.py")]) == 1


class TestSleepSeconds:
    def test_default(self):
        assert sleep_seconds("/SNS/VIS/shared/autoreduce/reduce_VIS.py", {}) == DEFAULT_SLEEP_SECONDS

    def test_global_override(self):
        assert sleep_seconds("/SNS/VIS/shared/autoreduce/reduce_VIS.py", {"REDUCE_SLEEP": "3"}) == 3.0

    def test_instrument_override_wins(self):
        env = {"REDUCE_SLEEP": "3", "REDUCE_SLEEP_CG2": "0.5"}
        assert sleep_seconds("/HFIR/CG2/shared/autoreduce/reduce_CG2.py", env) == 0.5
        assert sleep_seconds("/HFIR/CG3/shared/autoreduce/reduce_CG3.py", env) == 3.0

    def test_underscore_instrument(self):
        env = {"REDUCE_SLEEP_REF_L": "2"}
        assert sleep_seconds("/SNS/REF_L/shared/autoreduce/reduce_REF_L.py", env) == 2.0

    def test_run_like_the_agent_succeeds_with_empty_stderr(self, tmp_path):
        # run it the way the agent does; any stderr output fails the run
        # drop inherited overrides (the script's own name makes it look for REDUCE_SLEEP_SLEEP)
        env = {key: value for key, value in os.environ.items() if not key.startswith("REDUCE_SLEEP")}
        env["REDUCE_SLEEP"] = "0"
        result = subprocess.run(
            [sys.executable, SLEEP_SCRIPT, "/HFIR/CG2/IPTS-90102/nexus/CG2_1.nxs.h5", f"{tmp_path}/"],
            env=env,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert result.stderr == ""


class FakeConnection:
    """Stands in for stomp.Connection and keeps what was sent."""

    def __init__(self):
        self.sent = []

    def send(self, destination, body, headers):
        self.sent.append((destination, json.loads(body)))


def client(run_base=1000):
    c = LoadTestClient(run_base=run_base)
    c.conn = FakeConnection()
    return c


class TestRunNumbers:
    def test_new_block_every_minute(self):
        first = default_run_base(datetime(2026, 11, 17, 9, 0, 0, tzinfo=timezone.utc))
        same_minute = default_run_base(datetime(2026, 11, 17, 9, 0, 59, tzinfo=timezone.utc))
        next_minute = default_run_base(datetime(2026, 11, 17, 9, 1, 0, tzinfo=timezone.utc))
        assert first == same_minute
        assert next_minute - first == 1000

    def test_fits_a_32_bit_run_number_until_2030(self):
        assert default_run_base(datetime(2030, 1, 1, tzinfo=timezone.utc)) + 999 < 2**31

    def test_counts_up_per_instrument(self):
        c = client()
        numbers = [c.send_run(name)["run_number"] for name in ("cg2", "cg2", "eqsans", "cg2")]
        assert numbers == [1000, 1001, 1000, 1002]

    def test_explicit_run_number_is_kept(self):
        assert client().send_run("cg2", 42)["run_number"] == 42

    def test_explicit_run_number_is_not_reused(self):
        c = client()
        c.send_run("cg2", 1000)
        assert c.send_run("cg2")["run_number"] == 1001

    def test_explicit_run_number_does_not_move_the_counter_back(self):
        c = client()
        c.send_run("cg2")
        c.send_run("cg2")
        c.send_run("cg2", 42)
        assert c.send_run("cg2")["run_number"] == 1002

    def test_instrument_case_shares_one_counter(self):
        c = client()
        c.send_run("cg2")
        c.send_run("CG2", 1001)
        assert c.send_run("Cg2")["run_number"] == 1002

    def test_rejects_a_base_without_room_for_a_block(self):
        with pytest.raises(ValueError):
            client(run_base=2**31 - 1)
        client(run_base=2**31 - 1000)  # last base whose block still fits

    def test_never_generates_past_the_32_bit_limit(self):
        c = client()
        assert c.send_run("cg2", 2**31 - 1)["run_number"] == 2**31 - 1  # explicit max is fine
        with pytest.raises(ValueError):
            c.send_run("cg2")
        assert len(c.conn.sent) == 1


class TestSendRun:
    def test_fills_in_load_test_instruments(self):
        msg = client().send_run("cg2")
        assert (msg["facility"], msg["ipts"], msg["data_file"]) == ("HFIR", "IPTS-90102", lti.data_file("cg2"))

    def test_caller_values_win(self):
        msg = client().send_run("arcs", facility="SNS", ipts="IPTS-27800", data_file="/SNS/ARCS/x.nxs.h5")
        assert (msg["facility"], msg["ipts"], msg["data_file"]) == ("SNS", "IPTS-27800", "/SNS/ARCS/x.nxs.h5")

    def test_goes_to_the_workflow_manager(self):
        c = client()
        c.send_run("cg2")
        assert c.conn.sent[0][0] == "/queue/POSTPROCESS.DATA_READY"


class TestBaselineScenarios:
    def test_each_instrument_sends_one_run_per_load_test_instrument(self):
        sent = baseline_profile.send_workload(client(), "each-instrument", interleave=False)
        assert sorted(name for name, _ in sent) == sorted(lti.INSTRUMENTS)

    def test_scenarios_never_repeat_a_run(self):
        for scenario in baseline_profile.SCENARIOS:
            c = client()
            sent = baseline_profile.send_workload(c, scenario, interleave=(scenario == "fairness"))
            # check what went to the broker, not just what send_run returned
            on_the_wire = [(msg["instrument"], msg["run_number"]) for _, msg in c.conn.sent]
            assert len(set(on_the_wire)) == len(on_the_wire), scenario
            assert set(on_the_wire) == sent, scenario

    def test_timeout_names_runs_missing_from_the_database(self, monkeypatch, capsys):
        monkeypatch.setattr(baseline_profile.metrics, "fetch_run_events", lambda since, db: [])
        baseline_profile.wait_for_drain(None, {("cg2", 1000)}, None, timeout=0, poll_interval=0)
        assert "1 sent runs never reached the database: [('cg2', 1000)]" in capsys.readouterr().out
