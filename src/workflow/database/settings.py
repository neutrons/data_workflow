import os
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
    }
}

SECRET_KEY = os.environ.get("APP_SECRET")

TIME_ZONE = os.environ.get("TIME_ZONE")

USE_TZ = True

# Note: Django > 1.7 requires full package path 'workflow.database.report'
INSTALLED_APPS = ("workflow.database.report",)


# ActiveMQ settings
icat_user = "icat"
icat_passcode = "icat"
wkflow_user = "wkflowmgr"
wkflow_passcode = "wkflowmgr"
worker_user = "worker"
worker_passcode = "worker"

# Import local settings if available
# brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
brokers = list(map(tuple, json.loads(env_amq_broker)))
