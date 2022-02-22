# The DB settings are defined in the workflow manager
from dasmon_listener.amq_consumer import process_signal
from report.models import Instrument
from settings import INSTALLATION_DIR
import argparse
import logging
import sys
import os

TIME_ZONE = "America/New_York"
USE_TZ = True
INSTALLED_APPS = ("dasmon",)


if os.path.isfile("settings.py"):
    logging.warning("Using local settings.py file")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dasmon_listener.settings")

sys.path.append(INSTALLATION_DIR)


def process_sig(instrument, signal, message, sig_assert=True):
    instrument_id = Instrument.objects.get(name=instrument.lower())
    signal_dict = {
        "msg_type": "2147483648",
        "src_name": "DASMON.0",
        "timestamp": "1375464085",
        "sig_name": signal,
        "sig_source": "DAS",
    }
    if sig_assert:
        signal_dict["sig_message"] = message
        signal_dict["sig_level"] = "3"

    process_signal(instrument_id, signal_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dasmon Listener signal test")
    parser.add_argument("-n", metavar="name", help="Signal name", dest="name")
    parser.add_argument("-m", metavar="msg", help="message", dest="msg")
    parser.add_argument(
        "-b", metavar="instrument", help="instrument name", dest="instrument"
    )
    subparsers = parser.add_subparsers(dest="command", help="available sub-commands")
    subparsers.add_parser("assert", help="Assert a signal")
    subparsers.add_parser("retract", help="Retract a signal")
    namespace = parser.parse_args()

    msg = "Test error" if namespace.msg is None else namespace.msg
    sig = "TEST_SIGNAL" if namespace.name is None else namespace.name
    instrument = "seq" if namespace.instrument is None else namespace.instrument.lower()

    sig_assert = namespace.command == "assert"

    process_sig(instrument=instrument, signal=sig, message=msg, sig_assert=sig_assert)
