"""This configuration is meant for running the unittests outside of docker"""
from .base import *  # noqa
from .base import INSTALLED_APPS

# use sqllite for unit test runs
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 30000,
        },
    }
}

# This overrides the default and disables ldap
AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)
if "django_auth_ldap" in INSTALLED_APPS:
    INSTALLED_APPS.remove("django_auth_ldap")
