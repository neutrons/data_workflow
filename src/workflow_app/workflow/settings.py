# Django settings
import json

# Set logging level
import logging
import os

from .database.settings import *  # noqa: F401, F403

LOGGING_LEVEL = logging.INFO

# Default queue names
POSTPROCESS_INFO = "POSTPROCESS.INFO"
POSTPROCESS_ERROR = "POSTPROCESS.ERROR"
CATALOG_DATA_READY = "CATALOG.ONCAT.DATA_READY"
REDUCTION_DATA_READY = "REDUCTION.DATA_READY"
REDUCTION_CATALOG_DATA_READY = "REDUCTION_CATALOG.DATA_READY"

WKFLOW_USER = os.environ.get("WORKFLOW_USER")
WKFLOW_PASSCODE = os.environ.get("WORKFLOW_PASS")


_TRUTHY_VALUES = ("1", "true", "yes", "on")
_FALSY_VALUES = ("0", "false", "no", "off", "")


def _parse_env_flag(name, default=False):
    """
    Parse a boolean feature flag from the environment.

    Returns a ``(value, recognized)`` tuple. ``recognized`` is False when the
    variable is set to something we do not understand; in that case ``value`` is
    the supplied default, so a typo (for example ``ENABLE_..=ture``) fails safe to
    the default rather than raising.

    :param name: environment variable name
    :param default: value to return when the variable is unset or unrecognized
    :return: (bool value, bool recognized)
    """
    raw = os.environ.get(name)
    if raw is None:
        return default, True
    normalized = raw.strip().lower()
    if normalized in _TRUTHY_VALUES:
        return True, True
    if normalized in _FALSY_VALUES:
        return False, True
    return default, False


def _env_flag(name, default=False):
    """
    Read a boolean feature flag from the environment.

    Accepts common truthy/falsy spellings ("1"/"0", "true"/"false", "yes"/"no",
    "on"/"off"), case-insensitively. Any unset or unrecognized value returns the
    supplied default.

    :param name: environment variable name
    :param default: value to return when the variable is unset
    :return: bool
    """
    value, _recognized = _parse_env_flag(name, default=default)
    return value


# Per-instrument queue routing.
#
# When enabled, completed runs are routed to dedicated per-instrument queues
# (REDUCTION.<INSTRUMENT>.DATA_READY / REDUCTION_CATALOG.<INSTRUMENT>.DATA_READY)
# instead of the shared REDUCTION.DATA_READY / REDUCTION_CATALOG.DATA_READY queues.
#
# Defaults to OFF so that merging this change does not alter current behavior.
# DO NOT enable in any environment until the consumer side (post_processing_agent)
# is deployed and subscribed to the per-instrument queues -- otherwise routed
# messages accumulate with no consumer.
#
# Follow-up: this flag is a rollout and rollback control, not permanent config.
# Plan to deprecate and remove it once per-instrument routing has run clean for
# one full run cycle, so we are not left maintaining a branch that is never
# exercised in production.
ENABLE_PER_INSTRUMENT_QUEUES, _PER_INSTRUMENT_FLAG_RECOGNIZED = _parse_env_flag(
    "ENABLE_PER_INSTRUMENT_QUEUES", default=False
)
_PER_INSTRUMENT_FLAG_RAW = os.environ.get("ENABLE_PER_INSTRUMENT_QUEUES")


def log_effective_config():
    """
    Log the effective per-instrument routing configuration once, at startup.

    Called from the workflow manager entry point so operators can confirm which
    mode the process is running in from the very first log lines. A value we
    could not interpret is reported as a warning and treated as OFF (shared
    queues); it is never a fatal error, so a misconfigured flag degrades to
    current behavior instead of taking the manager down.
    """
    if not _PER_INSTRUMENT_FLAG_RECOGNIZED:
        logging.warning(
            "ENABLE_PER_INSTRUMENT_QUEUES=%r is not a recognized boolean; "
            "treating per-instrument routing as OFF (shared queues)",
            _PER_INSTRUMENT_FLAG_RAW,
        )
    if ENABLE_PER_INSTRUMENT_QUEUES:
        logging.info(
            "Per-instrument queue routing is ENABLED; reduction and reduction-catalog messages "
            "route to REDUCTION.<INSTRUMENT>.DATA_READY / REDUCTION_CATALOG.<INSTRUMENT>.DATA_READY "
            "(cataloging stays on the shared CATALOG.ONCAT.DATA_READY)"
        )
    else:
        logging.info("Per-instrument queue routing is DISABLED; all traffic uses the shared queues")


# configure activemq brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
BROKERS = list(map(tuple, json.loads(env_amq_broker)))
