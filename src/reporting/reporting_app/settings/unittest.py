"""This configuration is meant for running the unittests outside of docker"""
from .base import *  # noqa
from .base import INSTALLED_APPS

del DATABASES  # noqa: F821
# use sqllite for unit test runs
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "OPTIONS": {
            "timeout": 30000,
        },
    }
}

DEBUG = True

TIME_ZONE = "America/New_York"

CATALOG_URL = "catalog.test.xyz"
CATALOG_ID = "test"
CATALOG_SECRET = "test"

del CACHES  # noqa: F821

# This overrides the default and disables ldap
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
if "django_auth_ldap" in INSTALLED_APPS:
    INSTALLED_APPS.remove("django_auth_ldap")

validate_ldap_settings(server_uri=AUTH_LDAP_SERVER_URI, user_dn_template=AUTH_LDAP_USER_DN_TEMPLATE)  # noqa: F405
