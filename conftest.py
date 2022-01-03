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
    )
