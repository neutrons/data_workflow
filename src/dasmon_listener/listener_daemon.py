"""
    DASMON listener daemon
"""
import sys
import argparse

import logging
import logging.handlers

# Set log level
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("stomp.py").setLevel(logging.WARNING)

# Formatter
ft = logging.Formatter("%(asctime)-15s %(message)s")
# Create a log file handler
fh = logging.handlers.TimedRotatingFileHandler(
    "dasmon_listener.log", when="midnight", backupCount=15
)
fh.setLevel(logging.INFO)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)


from .amq_consumer import Client, Listener  # noqa: E402

# Daemon imports
from workflow.daemon import Daemon  # noqa: E402
from .settings import brokers  # noqa: E402
from .settings import amq_user  # noqa: E402
from .settings import amq_pwd  # noqa: E402
from .settings import queues  # noqa: E402


class DasMonListenerDaemon(Daemon):
    """
    DASMON listener daemon
    """

    def run(self):
        """
        Run the dasmon listener daemon
        """
        c = Client(brokers, amq_user, amq_pwd, queues, "dasmon_listener")
        c.set_listener(Listener())
        c.listen_and_wait(0.01)


def run():
    """
    Entry point for command line script
    """
    parser = argparse.ArgumentParser(description="DASMON listener")
    subparsers = parser.add_subparsers(dest="command", help="available sub-commands")
    subparsers.add_parser("start", help="Start daemon [-h for help]")
    subparsers.add_parser("restart", help="Restart daemon [-h for help]")
    subparsers.add_parser("stop", help="Stop daemon")
    namespace = parser.parse_args()

    # Start the daemon
    daemon = DasMonListenerDaemon("/tmp/dasmon_listener.pid", stdout=None, stderr=None)

    if namespace.command == "start":
        daemon.start()
    elif namespace.command == "stop":
        daemon.stop()
    elif namespace.command == "restart":
        daemon.restart()

    sys.exit(0)


if __name__ == "__main__":
    run()
