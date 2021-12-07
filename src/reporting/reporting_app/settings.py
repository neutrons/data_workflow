# Django settings for reporting_app project.
import os
import django
# The DB settings are defined in the workflow manager
from workflow.database.settings import DATABASES
DATABASES['default']['CONN_MAX_AGE'] = 5
# DATABASES['default']['CONN_MAX_AGE']=None

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = os.environ.get('DEBUG')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = os.environ.get('TIME_ZONE')

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/var/www/workflow/static/web_monitor'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/static/web_monitor/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = '/var/www/workflow/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static')),
    os.path.join(os.path.dirname(django.__file__), 'contrib', 'admin', 'static'),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn'

# ------- Template settings for Django 1.6 ------
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #     'django.template.loaders.eggs.Loader',
)
TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
)
# ------ End of template settings for Django 1.6 ------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'users.mobile_detection.DetectMobileBrowser',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'reporting_app.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'reporting_app.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django_auth_ldap',
    'report',
    'users',
    'dasmon',
    'pvmon',
    'file_handling',
    'reduction',
    # 'debug_toolbar',
)

AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_LDAP_SERVER_URI = ""
AUTH_LDAP_USER_DN_TEMPLATE = ""

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.4/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['*']

# Set the following to the local domain name
ALLOWED_DOMAIN = ''
LOGIN_URL = '/workflow/users/login'
LANDING_VIEW = 'dasmon:dashboard'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        },
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARN',
            'propagate': False,
        },
        'report': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'dasmon': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django_auth_ldap': {
            'handlers': ['console'],
            'level': 'WARN',
        },
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'webcache',
    }
}

# Timeout value for cached run and error rates, in seconds
RUN_RATE_CACHE_TIMEOUT = 120
# Timeout value for cached pages that are expected to be quick to render, in seconds
FAST_PAGE_CACHE_TIMEOUT = 10
# Timeout value for cached pages that are expected to be slow to render, in seconds
SLOW_PAGE_CACHE_TIMEOUT = 60

# QUERY TUNING - SAFE FOR POSTGRESQL
# If the tables IDs are always incrementing, use 'id' below
# otherwise use 'timestamp'
DASMON_SQL_SORT = 'id'
# DASMON_SQL_SORT = 'timestamp'

# REPORTING SETTINGS
# Amount of time displayed when plotting a live PV [seconds]
PVMON_PLOT_TIME_RANGE = 2 * 60 * 60
# Max number of old PV points to show when there were no points in defined time range
PVMON_NUMBER_OF_OLD_PTS = 20
# Amount of time displayed when plotting a live PV
DASMON_PLOT_TIME_RANGE = 2 * 60 * 60
# Max number of old PV points to show when there were no points in defined time range
DASMON_NUMBER_OF_OLD_PTS = 20

# MONITORING OPTION
MONITOR_ON = True

HEARTBEAT_TIMEOUT = 15

# Prefix for status parameter names for monitored sub-systems
SYSTEM_STATUS_PREFIX = 'system_'

# Instrument team user group suffix
INSTRUMENT_TEAM_SUFFIX = 'InstrumentTeam'

# Post-processing node prefix values (autoreduction and cataloging)
POSTPROCESS_NODE_PREFIX = ['autoreducer', 'fermi']

# ActiveMQ queue for generating a new reduction script
REDUCTION_SCRIPT_CREATION_QUEUE = '/queue/REDUCTION.CREATE_SCRIPT'

HELPLINE_EMAIL = 'adara_support@ornl.gov'

INSTRUMENT_REDUCTION_SETUP = ('seq', 'arcs', 'corelli', 'cncs', 'ref_m')

LIVE_DATA_SERVER = "/plots/$instrument/$run_number/update"
LIVE_DATA_SERVER_DOMAIN = "livedata.sns.gov"
LIVE_DATA_SERVER_PORT = "443"

# Link out to fitting application
FITTING_URLS = {}

# Import local settings if available
try:
    from local_settings import *  # noqa: F401, F403
    LOCAL_SETTINGS = True
except ImportError:
    LOCAL_SETTINGS = False
