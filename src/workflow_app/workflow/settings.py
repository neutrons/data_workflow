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
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# Per-instrument queue routing (see docs/per_instrument_queue_routing.md).
#
# When enabled, completed runs are routed to dedicated per-instrument queues
# (REDUCTION.<INSTRUMENT>.DATA_READY / REDUCTION_CATALOG.<INSTRUMENT>.DATA_READY)
# instead of the shared REDUCTION.DATA_READY / REDUCTION_CATALOG.DATA_READY queues.
#
# Defaults to OFF so that merging this change does not alter current behavior.
# DO NOT enable in any environment until the consumer side (post_processing_agent)
# is deployed and subscribed to the per-instrument queues -- otherwise routed
# messages accumulate with no consumer. See the rollout runbook.
ENABLE_PER_INSTRUMENT_QUEUES = _env_flag("ENABLE_PER_INSTRUMENT_QUEUES", default=False)

# configure activemq brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
BROKERS = list(map(tuple, json.loads(env_amq_broker)))
