from re import DEBUG
from django.conf import settings
import os


def pytest_configure():
    settings.configure(
        INSTALLED_APPS=(
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
        ),
        SECRET_KEY='-0zoc$fl2fa&amp;rmzeo#uh-qz-k+4^1)_9p1qwby1djzybqtl_nn',
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "OPTIONS": {  # for concurrent writes
                    "timeout": 30000,  # ms
                }
            }
        },
        #
        MIDDLEWARE = (
            'django.middleware.common.CommonMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            # Uncomment the next line for simple clickjacking protection:
            # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
            # 'debug_toolbar.middleware.DebugToolbarMiddleware',
        ),
        AUTHENTICATION_BACKENDS = (
            'django.contrib.auth.backends.ModelBackend',
        ),
        #
        DEBUG=True,
        #
        LANDING_VIEW="dasmon:dashboard",
        ROOT_URLCONF="reporting_app.urls",
        SLOW_PAGE_CACHE_TIMEOUT = 60,
        FAST_PAGE_CACHE_TIMEOUT = 10,
        HEARTBEAT_TIMEOUT = 15,
        SYSTEM_STATUS_PREFIX = 'system_',
        # Amount of time displayed when plotting a live PV
        DASMON_PLOT_TIME_RANGE = 2 * 60 * 60,
        DASMON_SQL_SORT = 'id',
        # Max number of old PV points to show when there were no points in defined time range
        DASMON_NUMBER_OF_OLD_PTS = 20,
        # Amount of time displayed when plotting a live PV [seconds]
        PVMON_PLOT_TIME_RANGE = 2 * 60 * 60,
        # Max number of old PV points to show when there were no points in defined time range
        PVMON_NUMBER_OF_OLD_PTS = 20,
        # Post-processing node prefix values (autoreduction and cataloging)
        POSTPROCESS_NODE_PREFIX = ['autoreducer', 'fermi'],
        # Timeout value for cached run and error rates, in seconds
        RUN_RATE_CACHE_TIMEOUT = 120,
        # Instrument team user group suffix
        INSTRUMENT_TEAM_SUFFIX = 'InstrumentTeam',
        # MONITORING OPTION
        MONITOR_ON = True,
        #
        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [os.path.abspath("./src/reporting/templates")],
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
        ],
        #
        LIVE_DATA_SERVER = "/plots/$instrument/$run_number/update",
        LIVE_DATA_SERVER_DOMAIN = "livedata.sns.gov",
        LIVE_DATA_SERVER_PORT = "443",
        #
        USE_TZ = True,
        #
        HELPLINE_EMAIL = 'adara_support@ornl.gov',
        #
        CATALOG_URL="catalog.test.xyz",
        CATALOG_ID="test",
        CATALOG_SECRET="test",
        INSTRUMENT_REDUCTION_SETUP = ('seq', 'arcs', 'corelli', 'cncs', 'ref_m'),
        REDUCTION_SCRIPT_CREATION_QUEUE = '/queue/REDUCTION.CREATE_SCRIPT',
    )
