
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',           #, 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.environ.get('DATABASE_NAME'),                      # Or path to database file if using sqlite3.
        'USER': os.environ.get('DATABASE_USER'),                      # Not used with sqlite3.
        'PASSWORD': os.environ.get('DATABASE_PASS'),                  # Not used with sqlite3.
        'HOST': os.environ.get('DATABASE_HOST'),                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': os.environ.get('DATABASE_PORT'),                      # Set to empty string for default. Not used with sqlite3.
        }
}

SECRET_KEY = os.environ.get('APP_SECRET')

TIME_ZONE = os.environ.get('TIME_ZONE')

USE_TZ = True

#Note: Django > 1.7 requires full package path 'workflow.database.report'
INSTALLED_APPS = (
    'workflow.database.report',
    )

"""
    ActiveMQ settings
"""
# List of brokers
brokers = [("localhost", 61613)] 

icat_user = "icat"
icat_passcode = "icat"
wkflow_user = "wkflowmgr"
wkflow_passcode = "wkflowmgr"
worker_user = "worker"
worker_passcode = "worker"

# Import local settings if available
try:
    from local_settings import *
except ImportError, e:
    LOCAL_SETTINGS = False
    pass

