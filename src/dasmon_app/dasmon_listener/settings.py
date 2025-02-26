# Django settings for reporting_app project.
import os  # noqa: F401
import django  # noqa: F401
import json

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",  # , 'mysql', 'sqlite3' or 'oracle'.
        "NAME": os.environ.get("DATABASE_NAME"),  # Or path to database file if using sqlite3.
        "USER": os.environ.get("DATABASE_USER"),  # Not used with sqlite3.
        "PASSWORD": os.environ.get("DATABASE_PASS"),  # Not used with sqlite3.
        # Set to empty string for localhost. Not used with sqlite3.
        "HOST": os.environ.get("DATABASE_HOST"),
        # Set to empty string for default. Not used with sqlite3.
        "PORT": os.environ.get("DATABASE_PORT"),
        # set the idle connection time in seconds
        "CONN_MAX_AGE": 25,
    }
}

SECRET_KEY = "-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn"

TIME_ZONE = "America/New_York"

USE_TZ = True

INSTALLED_APPS = (
    "reporting.report",
    "reporting.dasmon",
    "reporting.pvmon",
)


# ActiveMQ settings

AMQ_USER = os.environ.get("ICAT_USER")
AMQ_PWD = os.environ.get("ICAT_PASS")

# List of brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
BROKERS = list(map(tuple, json.loads(env_amq_broker)))  # noqa: F811

PING_TOPIC = "/topic/SNS.COMMON.STATUS.PING"
ACK_TOPIC = "/topic/SNS.COMMON.STATUS.ACK"
ALERT_EMAIL = []
FROM_EMAIL = ""

INSTALLATION_DIR = "/var/www/workflow/app"

PURGE_TIMEOUT = 0.5  # days
IMAGE_PURGE_TIMEOUT = 360

MIN_NOTIFICATION_LEVEL = 3

# queues
default_queues = [
    "/topic/ADARA.APP.DASMON.0",
    "/topic/ADARA.STATUS.DASMON.0",
    "/topic/ADARA.SIGNAL.DASMON.0",
]
env_amq_queue = os.environ.get("AMQ_QUEUE", json.dumps(default_queues))
QUEUES = json.loads(env_amq_queue)
