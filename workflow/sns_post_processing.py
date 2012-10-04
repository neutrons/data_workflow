#!/usr/bin/env python
from workflow_manager import WorkflowManager
from settings import brokers, icat_user, icat_passcode
from daemon import Daemon
import sys
import os
import argparse

# List of queues to listen to. Each queue must have a
# corresponding class in states.py
queues = ['POSTPROCESS.DATA_READY',
          'CATALOG.STARTED',
          'CATALOG.COMPLETE',
          'REDUCTION.STARTED',
          'REDUCTION.DISABLED',
          'REDUCTION.COMPLETE',
          'REDUCTION.NOT_NEEDED',
          'REDUCTION_CATALOG.STARTED',
          'REDUCTION_CATALOG.COMPLETE',
          'POSTPROCESS.INFO',
          'POSTPROCESS.ERROR']

class WorkflowDaemon(Daemon):
    def run(self):
        mng = WorkflowManager(brokers, icat_user, icat_passcode, queues, False)
        mng.processing_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SNS data workflow manager')
    
    # Location of the output directory, where we put the output.log and error.log files
    parser.add_argument('-o', metavar='output directory',
                        help='location of the output directory', dest='output_dir')
    
    parser.add_argument('command', choices=['start', 'stop', 'restart'])
    
    
    namespace =  parser.parse_args()

    stdout_file = None
    stderr_file = None
    if namespace.output_dir is not None:
        if not os.path.isdir(namespace.output_dir):
            os.makedirs(namespace.output_dir)
        stdout_file = os.path.join(namespace.output_dir, 'output.log')
        stderr_file = os.path.join(namespace.output_dir, 'error.log')
    
    daemon = WorkflowDaemon('/tmp/workflow.pid',
                            stdout=stdout_file,
                            stderr=stderr_file)
    
    if namespace.command == 'start':
        daemon.start()
    elif namespace.command == 'stop':
        daemon.stop()
    elif namespace.command == 'restart':
        daemon.restart()

    sys.exit(0)
