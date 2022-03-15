# Django settings for reporting_app project.
import os  # noqa: F401
import django  # noqa: F401
import json

# The DB settings are defined in the workflow manager
from workflow.database.settings import DATABASES

DATABASES["default"]["CONN_MAX_AGE"] = 25
# DATABASES['default']['CONN_MAX_AGE'] = None

SECRET_KEY = "-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn"

TIME_ZONE = "America/New_York"

USE_TZ = True

INSTALLED_APPS = (
    "report",
    "dasmon",
    "pvmon",
)


# ActiveMQ settings

# List of brokers
from workflow.database.settings import brokers  # noqa: F401, E402
from workflow.database.settings import icat_user as amq_user  # noqa: F401, E402
from workflow.database.settings import icat_passcode as amq_pwd  # noqa: F401, E402

PING_TOPIC = "/topic/SNS.COMMON.STATUS.PING"
ACK_TOPIC = "/topic/SNS.COMMON.STATUS.ACK"
ALERT_EMAIL = []
FROM_EMAIL = ""
queues = [
    "/topic/ADARA.APP.DASMON.0",
    "/topic/ADARA.STATUS.DASMON.0",
    "/topic/ADARA.SIGNAL.DASMON.0",
]

INSTALLATION_DIR = "/var/www/workflow/app"

PURGE_TIMEOUT = 7
IMAGE_PURGE_TIMEOUT = 360

MIN_NOTIFICATION_LEVEL = 3

# Try to import local settings from environment
# brokers
env_amq_broker = os.environ.get("AMQ_BROKER", None)
if env_amq_broker:
    brokers = list(map(tuple,json.loads(env_amq_broker)))

# queues
env_amq_queue = os.environ.get("AMQ_QUEUE", None)
if env_amq_queue:
    queues = json.loads(env_amq_queue)
