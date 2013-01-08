
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',      #, 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'reporting_db',                      # Or path to database file if using sqlite3.
        'USER': 'icat',                      # Not used with sqlite3.
        'PASSWORD': 'icat',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
        }
}

TIME_ZONE = 'America/New_York'

USE_TZ = True

INSTALLED_APPS = (
    'report',
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


