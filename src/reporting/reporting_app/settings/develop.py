"""This is the settings to be used for a local developer build inside of docker"""
from .base import *  # noqa
from django.core.exceptions import ImproperlyConfigured
import ldap
from os import environ


# we don't care about ldap TLS
AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER}

# set the remote worker to be a common account
# setting these will force all execution to happen as a single user
TEST_REMOTE_USER = environ.get("TEST_USER_NAME")
TEST_REMOTE_PASSWD = environ.get("TEST_USER_PASSWD")
if (not TEST_REMOTE_USER) or (not TEST_REMOTE_PASSWD):
    msg = "Remote worker is improperly configured for deveop environment "
    msg += f"USER={TEST_REMOTE_USER} PASS={TEST_REMOTE_PASSWD}"
    raise ImproperlyConfigured(msg)
JOB_HANDLING_HOST = "worker"
