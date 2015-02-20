
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

SECRET_KEY = '-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn'

TIME_ZONE = 'America/New_York'

USE_TZ = True

#Note: Django > 1.7 requires full package path 'workflow.database.report'
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


"""
    ICAT server settings
"""
ICAT_DOMAIN = 'icat.sns.gov'
ICAT_PORT = 2080

# Import local settings if available
try:
    from local_settings import *
except ImportError, e:
    LOCAL_SETTINGS = False
    pass

