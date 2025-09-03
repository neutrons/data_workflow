"""
DASMON listener daemon
"""

import argparse
import logging
import logging.handlers
import sys

import psutil

# Set log level
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("stomp.py").setLevel(logging.WARNING)

# Formatter
ft = logging.Formatter("%(asctime)-15s %(message)s")
# Create a stream handler for stdout
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(ft)
logging.getLogger().addHandler(sh)
# Create a log file handler
fh = logging.handlers.TimedRotatingFileHandler("dasmon_listener.log", when="midnight", backupCount=15)
fh.setLevel(logging.INFO)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)

from .amq_consumer import Client, Listener  # noqa: E402
from .settings import (
    AMQ_PWD,  # noqa: E402
    AMQ_USER,  # noqa: E402
    BROKERS,  # noqa: E402
    QUEUES,  # noqa: E402
)


def start():
    c = Client(BROKERS, AMQ_USER, AMQ_PWD, QUEUES, "dasmon_listener")
    c.set_listener(Listener())  # Processes incoming messages from the ActiveMQ broker
    c.listen_and_wait(0.01)


def status():
    # check if running by checking for a process with the name dasmon_listener
    for proc in psutil.process_iter():
        if proc.name() == "dasmon_listener":
            logging.info("dasmon_listener is running with PID %d", proc.pid)
            sys.exit(0)

    logging.error("dasmon_listener is not running")
    sys.exit(1)


def run():
    """
    Entry point for command line script
    """
    parser = argparse.ArgumentParser(description="DASMON listener")
    subparsers = parser.add_subparsers(dest="command", help="available sub-commands")
    subparsers.add_parser("start", help="Start daemon [-h for help]")
    subparsers.add_parser("status", help="Show running status of daemon")
    namespace = parser.parse_args()

    if namespace.command == "start":
        start()
    elif namespace.command == "status":
        status()


if __name__ == "__main__":
    run()
