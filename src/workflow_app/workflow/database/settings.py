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
ICAT_USER = os.environ.get("ICAT_USER")
ICAT_PASSCODE = os.environ.get("ICAT_PASS")
WKFLOW_USER = os.environ.get("WORKFLOW_USER")
WKFLOW_PASSCODE = os.environ.get("WORKFLOW_PASS")
WORKER_USER = os.environ.get("WORKER_USER")
WORKER_PASSCODE = os.environ.get("WORKER_PASS")


# Configure activemq brokers
default_brokers = [("amqbroker1.sns.gov", 61613), ("amqbroker2.sns.gov", 61613)]
env_amq_broker = os.environ.get("AMQ_BROKER", json.dumps(default_brokers))
BROKERS = list(map(tuple, json.loads(env_amq_broker)))
