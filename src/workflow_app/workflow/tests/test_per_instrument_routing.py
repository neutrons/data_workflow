"""
Unit tests for per-instrument queue routing in workflow.states.

Covers:
* instrument extraction and validation (get_instrument_from_message)
* queue-name generation (get_instrument_queue_name)
* routing decisions for each handler with the feature flag ON and OFF
* both fallback paths (flag off, and instrument missing/invalid) and the warning log
* the env-driven feature flag parser (settings._env_flag) and its default (OFF)
"""

import json
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

    def test_unknown_queue_type_raises(self):
        with pytest.raises(ValueError):
            self.action.get_instrument_queue_name("eqsans", "bogus")


class ResolveReductionQueueTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

    def setUp(self):
        from workflow.states import StateAction

        self.action = StateAction()

    def test_flag_off_returns_shared_queue(self):
        message = json.dumps({"instrument": "eqsans"})
        with _patch_flag(False):
            assert self.action.resolve_reduction_queue(message, "SHARED", "reduction") == "SHARED"

    def test_flag_off_does_not_warn(self):
        message = json.dumps({"run_number": 1})  # no instrument
        with _patch_flag(False):
            self.caplog.clear()
            self.action.resolve_reduction_queue(message, "SHARED", "reduction")
        assert "falling back" not in self.caplog.text

    def test_flag_on_valid_instrument(self):
        message = json.dumps({"instrument": "eqsans"})
        with _patch_flag(True):
            assert self.action.resolve_reduction_queue(message, "SHARED", "reduction") == "REDUCTION.EQSANS.DATA_READY"

    def test_flag_on_missing_instrument_falls_back_and_warns(self):
        message = json.dumps({"run_number": 1})
        with _patch_flag(True):
            self.caplog.clear()
            result = self.action.resolve_reduction_queue(message, "SHARED", "reduction")
        assert result == "SHARED"
        assert "falling back to shared queue" in self.caplog.text.lower()


class PostprocessDataReadyRoutingTest(TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self.caplog = caplog

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
        with _patch_flag(True):
            self.caplog.clear()
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        reduction_dests = [d for d in sent if "REDUCTION" in d]
        assert reduction_dests == ["/queue/REDUCTION.DATA_READY"]
        assert "falling back to shared queue" in self.caplog.text.lower()

    def test_always_sends_both_catalog_and_reduction(self):
        handler, sent = self._make_handler()
        message = json.dumps({"instrument": "eqsans", "run_number": 1, "facility": "SNS"})
        with _patch_flag(True):
            handler({"destination": "/queue/POSTPROCESS.DATA_READY"}, message)
        assert len(sent) == 2


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
