"""This is the settings to be used for a remote production deploy"""

from .base import *  # noqa
from os import environ

# symbols to make flake8 happy
from .base import SECRET_KEY

if not SECRET_KEY or SECRET_KEY == "UNSET_SECRET":
    raise RuntimeError("APP_SECRET is not set")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = environ.get("DEBUG", False)

validate_ldap_settings(server_uri=AUTH_LDAP_SERVER_URI, user_dn_template=AUTH_LDAP_USER_DN_TEMPLATE)  # noqa: F405
