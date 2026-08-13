"""
Unit tests for per-instrument queue routing in workflow.states.

Covers:
* instrument extraction and validation (get_instrument_from_message)
* queue-name generation (get_instrument_queue_name)
* routing decisions for each handler with the feature flag ON and OFF
* both fallback paths (flag off, and instrument missing/invalid) and the warning log
* the standardized routing-decision log format and its rate limiting
* startup configuration validation and the effective-config echo
* error handling in send() (no connection, failed broker send, non-JSON body)
* the env-driven feature flag parser (settings._env_flag) and its default (OFF)
"""

import json
import logging
from unittest import mock

import pytest
from django.test import TestCase

import workflow

_ = [workflow]


def _patch_flag(value):
    """Context manager toggling the per-instrument routing feature flag.

    The handlers read ``settings.ENABLE_PER_INSTRUMENT_QUEUES`` at call time, so
    patching the module attribute is enough -- no re-import required.
    """
    return mock.patch("workflow.settings.ENABLE_PER_INSTRUMENT_QUEUES", value)


class InstrumentExtractionTest(TestCase):
    def setUp(self):
        from workflow.states import StateAction

        self.action = StateAction()

    def test_valid_instrument(self):
        message = json.dumps({"instrument": "eqsans", "run_number": 12345, "facility": "SNS"})
        assert self.action.get_instrument_from_message(message) == "eqsans"

    def test_instrument_is_lowercased(self):
        message = json.dumps({"instrument": "EQSANS"})
        assert self.action.get_instrument_from_message(message) == "eqsans"

    def test_instrument_with_digits(self):
        # HFIR instruments such as CG2 / HB2C contain digits and must be accepted.
        message = json.dumps({"instrument": "CG2"})
        assert self.action.get_instrument_from_message(message) == "cg2"

    def test_surrounding_whitespace_is_stripped(self):
        message = json.dumps({"instrument": "  arcs  "})
        assert self.action.get_instrument_from_message(message) == "arcs"

    def test_missing_instrument_field(self):
        message = json.dumps({"run_number": 12345})
        assert self.action.get_instrument_from_message(message) is None

    def test_empty_instrument(self):
        message = json.dumps({"instrument": ""})
        assert self.action.get_instrument_from_message(message) is None

    def test_whitespace_only_instrument(self):
        message = json.dumps({"instrument": "   "})
        assert self.action.get_instrument_from_message(message) is None

    def test_non_string_instrument(self):
        message = json.dumps({"instrument": 12345})
        assert self.action.get_instrument_from_message(message) is None

    def test_invalid_json(self):
        assert self.action.get_instrument_from_message("not-json") is None

    def test_non_dict_json(self):
        assert self.action.get_instrument_from_message(json.dumps(["eqsans"])) is None

    def test_non_string_message(self):
        assert self.action.get_instrument_from_message(None) is None

    def test_instrument_with_queue_delimiter_rejected(self):
        # A "." would create an unintended queue-name hierarchy.
        message = json.dumps({"instrument": "eqsans.data_ready"})
        assert self.action.get_instrument_from_message(message) is None

    def test_instrument_with_path_injection_rejected(self):
        message = json.dumps({"instrument": "eqsans/queue/evil"})
        assert self.action.get_instrument_from_message(message) is None

    def test_instrument_with_wildcard_rejected(self):
        # "*" and "#" are ActiveMQ Artemis wildcard characters.
        assert self.action.get_instrument_from_message(json.dumps({"instrument": "*"})) is None
        assert self.action.get_instrument_from_message(json.dumps({"instrument": "eq#sans"})) is None

    def test_instrument_with_underscore_allowed(self):
        # REF_L / REF_M are real SNS instruments; underscore is safe in queue names.
        assert self.action.get_instrument_from_message(json.dumps({"instrument": "REF_L"})) == "ref_l"
        assert self.action.get_instrument_from_message(json.dumps({"instrument": "ref_m"})) == "ref_m"


class QueueNameGenerationTest(TestCase):
    def setUp(self):
        from workflow.states import StateAction

        self.action = StateAction()

    def test_reduction_queue_name(self):
        assert self.action.get_instrument_queue_name("eqsans", "reduction") == "REDUCTION.EQSANS.DATA_READY"
        assert self.action.get_instrument_queue_name("cg2", "reduction") == "REDUCTION.CG2.DATA_READY"

    def test_reduction_catalog_queue_name(self):
        assert (
            self.action.get_instrument_queue_name("eqsans", "reduction_catalog")
            == "REDUCTION_CATALOG.EQSANS.DATA_READY"
        )

    def test_catalog_queue_name(self):
        assert self.action.get_instrument_queue_name("venus", "catalog") == "CATALOG.VENUS.DATA_READY"

    def test_default_queue_type_is_reduction(self):
        assert self.action.get_instrument_queue_name("nom") == "REDUCTION.NOM.DATA_READY"

    def test_underscore_instrument_queue_name(self):
        assert self.action.get_instrument_queue_name("ref_l", "reduction") == "REDUCTION.REF_L.DATA_READY"
        assert (
            self.action.get_instrument_queue_name("ref_l", "reduction_catalog") == "REDUCTION_CATALOG.REF_L.DATA_READY"
        )

    def test_unknown_queue_type_raises(self):
        with pytest.raises(ValueError):
            self.action.get_instrument_queue_name("eqsans", "bogus")


class ResolveReductionQueueTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def setUp(self):
        import workflow.states as states

        states._routing_log_throttle.reset()
        self.action = states.StateAction()

    def test_flag_off_returns_shared_queue(self):
        message = json.dumps({"instrument": "eqsans"})
        with _patch_flag(False):
            assert self.action.resolve_reduction_queue(message, "SHARED", "reduction") == "SHARED"

    def test_flag_off_logs_no_routing_decision(self):
        message = json.dumps({"run_number": 1})  # no instrument
        with _patch_flag(False):
            self.caplog.clear()
            self.action.resolve_reduction_queue(message, "SHARED", "reduction")
        assert "per_instrument_routing" not in self.caplog.text

    def test_flag_on_valid_instrument(self):
        message = json.dumps({"instrument": "eqsans"})
        with _patch_flag(True):
            assert self.action.resolve_reduction_queue(message, "SHARED", "reduction") == "REDUCTION.EQSANS.DATA_READY"

    def test_flag_on_missing_instrument_falls_back_and_warns(self):
        message = json.dumps({"run_number": 1})
        with _patch_flag(True), self.caplog.at_level(logging.WARNING):
            self.caplog.clear()
            result = self.action.resolve_reduction_queue(message, "SHARED", "reduction")
        assert result == "SHARED"
        # Standardized, greppable key=value line at WARNING level.
        assert "per_instrument_routing decision=fallback" in self.caplog.text
        assert "queue=SHARED" in self.caplog.text
        assert "reason=no_valid_instrument" in self.caplog.text


class PostprocessDataReadyRoutingTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def setUp(self):
        import workflow.states as states

        states._routing_log_throttle.reset()

    def _make_handler(self):
        from workflow.states import Postprocess_data_ready

        handler = Postprocess_data_ready()
        sent = []
        handler.send = lambda destination, message, persistent="true": sent.append(destination)
        return handler, sent

    def test_flag_on_routes_reduction_per_instrument(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "cg2", "run_number": 5678, "facility": "HFIR"})
        with _patch_flag(True):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        reduction_dests = [d for d in sent if "REDUCTION" in d]
        assert reduction_dests == ["/queue/REDUCTION.CG2.DATA_READY"]

    def test_flag_on_catalog_stays_shared(self):
        from workflow.states import CATALOG_DATA_READY

        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 1, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        catalog_dests = [d for d in sent if "CATALOG" in d]
        assert catalog_dests == ["/queue/%s" % CATALOG_DATA_READY]

    def test_flag_off_reduction_uses_shared(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 1, "facility": "SNS"})
        with _patch_flag(False):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        reduction_dests = [d for d in sent if "REDUCTION" in d]
        assert reduction_dests == ["/queue/REDUCTION.DATA_READY"]

    def test_flag_on_missing_instrument_falls_back(self):
        handler, sent = self._make_handler()
        message = json.dumps({"run_number": 1})
        with _patch_flag(True), self.caplog.at_level(logging.WARNING):
            self.caplog.clear()
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        reduction_dests = [d for d in sent if "REDUCTION" in d]
        assert reduction_dests == ["/queue/REDUCTION.DATA_READY"]
        assert "per_instrument_routing decision=fallback" in self.caplog.text

    def test_always_sends_both_catalog_and_reduction(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 1, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        assert len(sent) == 2

    def test_flag_on_routes_underscore_instrument_per_instrument(self):
        # REF_L must route to its own queue, not fall back to the shared queue.
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "REF_L", "run_number": 1, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        reduction_dests = [d for d in sent if "REDUCTION" in d]
        assert reduction_dests == ["/queue/REDUCTION.REF_L.DATA_READY"]


class ReductionRequestRoutingTest(TestCase):
    def _make_handler(self):
        from workflow.states import Reduction_request

        handler = Reduction_request()
        sent = []
        handler.send = lambda destination, message, persistent="true": sent.append(destination)
        return handler, sent

    def test_flag_on_routes_per_instrument(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 100, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/REDUCTION.REQUEST"}, message)
        assert sent == ["/queue/REDUCTION.EQSANS.DATA_READY"]

    def test_flag_off_uses_shared(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 100, "facility": "SNS"})
        with _patch_flag(False):
            handler({"destination": "/queue/REDUCTION.REQUEST"}, message)
        assert sent == ["/queue/REDUCTION.DATA_READY"]

    def test_flag_on_missing_instrument_uses_shared(self):
        handler, sent = self._make_handler()
        message = json.dumps({"run_number": 100})
        with _patch_flag(True):
            handler({"destination": "/queue/REDUCTION.REQUEST"}, message)
        assert sent == ["/queue/REDUCTION.DATA_READY"]


class ReductionCompleteRoutingTest(TestCase):
    def _make_handler(self):
        from workflow.states import Reduction_complete

        handler = Reduction_complete()
        sent = []
        handler.send = lambda destination, message, persistent="true": sent.append(destination)
        return handler, sent

    def test_flag_on_routes_per_instrument_catalog(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 100, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/REDUCTION.COMPLETE"}, message)
        assert sent == ["/queue/REDUCTION_CATALOG.EQSANS.DATA_READY"]

    def test_flag_off_uses_shared_catalog(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 100, "facility": "SNS"})
        with _patch_flag(False):
            handler({"destination": "/queue/REDUCTION.COMPLETE"}, message)
        assert sent == ["/queue/REDUCTION_CATALOG.DATA_READY"]

    def test_flag_on_missing_instrument_uses_shared_catalog(self):
        handler, sent = self._make_handler()
        message = json.dumps({"run_number": 100})
        with _patch_flag(True):
            handler({"destination": "/queue/REDUCTION.COMPLETE"}, message)
        assert sent == ["/queue/REDUCTION_CATALOG.DATA_READY"]


class FeatureFlagConfigTest(TestCase):
    """The flag must be environment-driven and default OFF (never hardcoded on)."""

    def test_default_is_off(self):
        from workflow.settings import _env_flag

        with mock.patch.dict("os.environ", {}, clear=True):
            assert _env_flag("ENABLE_PER_INSTRUMENT_QUEUES") is False

    def test_truthy_spellings(self):
        from workflow.settings import _env_flag

        for value in ("1", "true", "True", "TRUE", "yes", "on", "  true  "):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                assert _env_flag("FLAG") is True, value

    def test_falsy_spellings(self):
        from workflow.settings import _env_flag

        for value in ("0", "false", "False", "no", "off", "", "banana"):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                assert _env_flag("FLAG") is False, value

    def test_unrecognized_value_returns_caller_default(self):
        # An unrecognized value must honor the caller's default rather than
        # silently returning False (matches the docstring).
        from workflow.settings import _env_flag

        with mock.patch.dict("os.environ", {"FLAG": "banana"}):
            assert _env_flag("FLAG", default=True) is True
            assert _env_flag("FLAG", default=False) is False

    def test_module_default_is_off(self):
        # The shipped default value of the setting must be False so that merging
        # this change does not alter production behavior.
        import importlib

        from workflow import settings as workflow_settings

        with mock.patch.dict("os.environ", {}, clear=True):
            importlib.reload(workflow_settings)
            assert workflow_settings.ENABLE_PER_INSTRUMENT_QUEUES is False
        # Reload once more so other tests see a clean module state.
        importlib.reload(workflow_settings)


class RoutingLogFormatTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def setUp(self):
        import workflow.states as states

        states._routing_log_throttle.reset()
        self.action = states.StateAction()

    def test_per_instrument_decision_logged_at_info(self):
        message = json.dumps({"instrument": "eqsans"})
        with _patch_flag(True), self.caplog.at_level(logging.INFO):
            self.action.resolve_reduction_queue(message, "REDUCTION.DATA_READY", "reduction")
        text = self.caplog.text
        assert "per_instrument_routing decision=per_instrument" in text
        assert "instrument=eqsans" in text
        assert "queue=REDUCTION.EQSANS.DATA_READY" in text
        assert "reason=ok" in text


class RoutingLogThrottleTest(TestCase):
    def test_logs_first_then_every_nth_with_suppressed_counts(self):
        from workflow.states import _RoutingLogThrottle

        throttle = _RoutingLogThrottle(every=3)
        results = [throttle.record("k") for _ in range(7)]
        assert results == [
            (True, 0),  # first occurrence always logs
            (False, 0),
            (True, 1),  # 3rd: logs, 1 suppressed since last emit
            (False, 0),
            (False, 0),
            (True, 2),  # 6th: logs, 2 suppressed since last emit
            (False, 0),
        ]

    def test_keys_are_independent(self):
        from workflow.states import _RoutingLogThrottle

        throttle = _RoutingLogThrottle(every=100)
        assert throttle.record("a") == (True, 0)
        assert throttle.record("b") == (True, 0)


class RoutingLogSpamControlTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def setUp(self):
        import workflow.states as states

        states._routing_log_throttle.reset()
        self.action = states.StateAction()

    def test_repeated_fallbacks_do_not_flood_the_log(self):
        message = json.dumps({"run_number": 1})  # no instrument -> fallback every time
        with _patch_flag(True), self.caplog.at_level(logging.WARNING):
            for _ in range(1000):
                self.action.resolve_reduction_queue(message, "REDUCTION.DATA_READY", "reduction")
        warnings = [
            r
            for r in self.caplog.records
            if r.levelno == logging.WARNING and "per_instrument_routing" in r.getMessage()
        ]
        # 1000 identical fallbacks must not produce anywhere near 1000 log lines.
        assert 0 < len(warnings) <= 5
        assert any("suppressed=" in r.getMessage() for r in warnings)


class StartupConfigValidationTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def test_parse_env_flag_unset_uses_default_and_is_recognized(self):
        from workflow.settings import _parse_env_flag

        with mock.patch.dict("os.environ", {}, clear=True):
            assert _parse_env_flag("FLAG") == (False, True)
            assert _parse_env_flag("FLAG", default=True) == (True, True)

    def test_parse_env_flag_recognized_values(self):
        from workflow.settings import _parse_env_flag

        for value in ("1", "true", "On", "  YES "):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                assert _parse_env_flag("FLAG") == (True, True), value
        for value in ("0", "false", "off", ""):
            with mock.patch.dict("os.environ", {"FLAG": value}):
                assert _parse_env_flag("FLAG") == (False, True), value

    def test_parse_env_flag_unrecognized_is_flagged_and_fails_safe(self):
        from workflow.settings import _parse_env_flag

        with mock.patch.dict("os.environ", {"FLAG": "ture"}):
            value, recognized = _parse_env_flag("FLAG", default=False)
            assert value is False
            assert recognized is False

    def test_log_effective_config_reports_enabled(self):
        from workflow import settings

        with (
            mock.patch.multiple(settings, ENABLE_PER_INSTRUMENT_QUEUES=True, _PER_INSTRUMENT_FLAG_RECOGNIZED=True),
            self.caplog.at_level(logging.INFO),
        ):
            self.caplog.clear()
            settings.log_effective_config()
        assert "ENABLED" in self.caplog.text

    def test_log_effective_config_reports_disabled(self):
        from workflow import settings

        with (
            mock.patch.multiple(settings, ENABLE_PER_INSTRUMENT_QUEUES=False, _PER_INSTRUMENT_FLAG_RECOGNIZED=True),
            self.caplog.at_level(logging.INFO),
        ):
            self.caplog.clear()
            settings.log_effective_config()
        assert "DISABLED" in self.caplog.text

    def test_log_effective_config_warns_on_unrecognized_value(self):
        from workflow import settings

        with (
            mock.patch.multiple(
                settings,
                ENABLE_PER_INSTRUMENT_QUEUES=False,
                _PER_INSTRUMENT_FLAG_RECOGNIZED=False,
                _PER_INSTRUMENT_FLAG_RAW="ture",
            ),
            self.caplog.at_level(logging.WARNING),
        ):
            self.caplog.clear()
            settings.log_effective_config()
        assert "not a recognized boolean" in self.caplog.text
        assert "ture" in self.caplog.text


class SendErrorHandlingTest(TestCase):
    @mock.patch("workflow.database.transactions.add_status_entry")
    def test_no_connection_records_error_entry(self, mock_add):
        from workflow.states import StateAction

        StateAction().send("REDUCTION.DATA_READY", json.dumps({"run_number": 1}))
        assert mock_add.called
        headers = mock_add.call_args[0][0]
        assert "POSTPROCESS.ERROR" in headers["destination"]

    @mock.patch("workflow.database.transactions.add_status_entry")
    def test_no_connection_with_non_json_message_does_not_raise(self, mock_add):
        from workflow.states import StateAction

        StateAction().send("REDUCTION.DATA_READY", "not-json")  # must not raise
        assert mock_add.called

    @mock.patch("workflow.database.transactions.add_status_entry")
    def test_broker_send_failure_is_contained(self, mock_add):
        from workflow.states import StateAction

        connection = mock.Mock()
        connection.send.side_effect = RuntimeError("broker down")
        # Should not raise even though the broker send fails.
        StateAction(connection=connection).send("REDUCTION.EQSANS.DATA_READY", json.dumps({"run_number": 1}))
        headers = mock_add.call_args[0][0]
        assert "POSTPROCESS.ERROR" in headers["destination"]

    @mock.patch("workflow.database.transactions.add_status_entry")
    def test_successful_send_records_destination(self, mock_add):
        from workflow.states import StateAction

        connection = mock.Mock()
        StateAction(connection=connection).send("REDUCTION.EQSANS.DATA_READY", json.dumps({"run_number": 1}))
        connection.send.assert_called_once()
        headers = mock_add.call_args[0][0]
        assert headers["destination"] == "REDUCTION.EQSANS.DATA_READY"

    @mock.patch("workflow.database.transactions.add_status_entry", side_effect=KeyError("instrument"))
    def test_error_recording_failure_is_contained(self, mock_add):
        # add_status_entry raises on a message missing instrument/ipts/run_number.
        # Recording the error must not itself raise (containment guarantee).
        from workflow.states import StateAction

        StateAction().send("REDUCTION.DATA_READY", json.dumps({"run_number": 1}))
        assert mock_add.called

    @mock.patch("workflow.database.transactions.add_status_entry", side_effect=Exception("db down"))
    def test_broker_failure_with_db_down_is_contained(self, mock_add):
        # The outage case: broker send fails and the DB is unavailable too. Neither
        # can be allowed to propagate out of send().
        from workflow.states import StateAction

        connection = mock.Mock()
        connection.send.side_effect = RuntimeError("broker down")
        StateAction(connection=connection).send("REDUCTION.EQSANS.DATA_READY", json.dumps({"run_number": 1}))
        assert mock_add.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
