"""This is the settings to be used for a local developer build inside of docker"""

from .base import *  # noqa
import ldap


# we don't care about ldap TLS
AUTH_LDAP_GLOBAL_OPTIONS = {ldap.OPT_X_TLS_REQUIRE_CERT: ldap.OPT_X_TLS_NEVER}

# don't cache views, can obstruct debugging
FAST_PAGE_CACHE_TIMEOUT = 0
SLOW_PAGE_CACHE_TIMEOUT = 0

validate_ldap_settings(server_uri=AUTH_LDAP_SERVER_URI, user_dn_template=AUTH_LDAP_USER_DN_TEMPLATE)  # noqa: F405
