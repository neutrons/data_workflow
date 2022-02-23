"""This is the settings to be used for a remote test deploy"""
from .base import *  # noqa

# symbols to make flake8 happy
from .base import SECRET_KEY

if not SECRET_KEY or SECRET_KEY == "UNSET_SECRET":
    raise RuntimeError("APP_SECRET is not set")
