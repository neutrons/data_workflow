from django.conf import settings


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
        # Post-processing node prefix values (autoreduction and cataloging)
        POSTPROCESS_NODE_PREFIX = ['autoreducer', 'fermi'],
        # Timeout value for cached run and error rates, in seconds
        RUN_RATE_CACHE_TIMEOUT = 120,
        # Instrument team user group suffix
        INSTRUMENT_TEAM_SUFFIX = 'InstrumentTeam'
    )
