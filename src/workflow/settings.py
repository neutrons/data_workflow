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

wkflow_user = os.environ.get("WORKFLOW_USER")
wkflow_passcode = os.environ.get("WORKFLOW_PASS")

# configure activemq brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
brokers = list(map(tuple, json.loads(env_amq_broker)))
