# Django settings
from .database.settings import *  # noqa: F401, F403

# Set logging level
import logging
import os
import json

LOGGING_LEVEL = logging.INFO

# Default queue names
POSTPROCESS_INFO = "POSTPROCESS.INFO"
POSTPROCESS_ERROR = "POSTPROCESS.ERROR"
CATALOG_DATA_READY = "CATALOG.DATA_READY"
REDUCTION_DATA_READY = "REDUCTION.DATA_READY"
REDUCTION_CATALOG_DATA_READY = "REDUCTION_CATALOG.DATA_READY"

# Import local settings from environment
# brokers
env_amq_broker = os.environ.get("AMQ_BROKER", None)
if env_amq_broker:
    brokers = list(map(tuple, json.loads(env_amq_broker)))
