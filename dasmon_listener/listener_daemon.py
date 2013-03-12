"""
    DASMON listener daemon
"""
import sys
import argparse

import logging
# Set log level
logging.getLogger().setLevel(logging.INFO)
# Formatter
ft = logging.Formatter('%(asctime)-15s %(message)s')
# Create a log file handler
fh = logging.FileHandler('dasmon_listener.log')
fh.setLevel(logging.INFO)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)

from amq_consumer import Client, Listener

# Daemon imports
from workflow.daemon import Daemon
from settings import brokers
from settings import amq_user
from settings import amq_pwd
from settings import queues
from settings import instrument_shortname

class DasMonListenerDaemon(Daemon):
    instrument = ''
    def run(self):
        """
            Run the dasmon listener daemon
        """
        c = Client(brokers, amq_user, amq_pwd, 
                   queues, "dasmon_listener")
        c.set_listener(Listener(self.instrument))
        c.listen_and_wait(0.1)


if __name__ == "__main__": 
    parser = argparse.ArgumentParser(description='DASMON listener')
    subparsers = parser.add_subparsers(dest='command', help='available sub-commands')
    subparsers.add_parser('start', help='Start daemon [-h for help]')
    subparsers.add_parser('restart', help='Restart daemon [-h for help]')
    subparsers.add_parser('stop', help='Stop daemon')
    namespace = parser.parse_args()
    
    # Start the daemon
    daemon = DasMonListenerDaemon('/tmp/dasmon_listener.pid',
                                  stdout=None,
                                  stderr=None)
        
    # Make sure we store the info with the right instrument
    daemon.instrument = instrument_shortname
   
    if namespace.command == 'start':
        daemon.start()
    elif namespace.command == 'stop':
        daemon.stop()
    elif namespace.command == 'restart':
        daemon.restart()

    sys.exit(0)

