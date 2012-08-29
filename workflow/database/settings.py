# specified db engine
#db_engine = 'django.db.backends.postgresql_psycopg2'
db_engine = 'django.db.backends.mysql'
#db_engine = 'django.db.backends.sqlite3'
#db_engine = 'django.db.backends.oracle'

DATABASES = {
    'default': {
        'ENGINE': db_engine,      #, 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'reporting_db',                      # Or path to database file if using sqlite3.
        'USER': 'icat',                      # Not used with sqlite3.
        'PASSWORD': 'icat',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
}

TIME_ZONE = 'America/New_York'

USE_TZ = True

INSTALLED_APPS = (
    'report',
    )

