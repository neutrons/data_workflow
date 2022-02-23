"""This is the settings to be used for a local developer build inside of docker"""
from .base import *  # noqa
import ldap

# we don't care about ldap TLS
AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER}
