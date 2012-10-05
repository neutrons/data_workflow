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
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null',
                 check_frequency=None, workflow_recovery=False):
        super(WorkflowDaemon, self).__init__(pidfile, stdin, stdout, stderr)
        self._check_frequency = check_frequency
        self._workflow_recovery = workflow_recovery
        
    def run(self):
        check_frequency = 24
        workflow_check = False
        if self._check_frequency is not None:
            check_frequency = self._check_frequency
            workflow_check = True
            
        mng = WorkflowManager(brokers, icat_user, icat_passcode, queues, 
                              workflow_check=workflow_check,
                              check_frequency=check_frequency,
                              workflow_recovery=self._workflow_recovery)
        mng.processing_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SNS data workflow manager')
    
    # Location of the output directory, where we put the output.log and error.log files
    parser.add_argument('-o', metavar='directory',
                        help='location of the output directory',
                        dest='output_dir')
    
    parser.add_argument('command', choices=['start', 'stop', 'restart'])
    
    # Workflow verification and recovery options
    parser.add_argument('-f', metavar='hours',
                        help='number of hours between workflow checks',
                        type=int, dest='check_frequency')
    
    parser.add_argument('-r', help='try to recover from workflow problems',
                        action='store_true', dest='recover')
    
    namespace =  parser.parse_args()
    print namespace

    stdout_file = None
    stderr_file = None
    if namespace.output_dir is not None:
        if not os.path.isdir(namespace.output_dir):
            os.makedirs(namespace.output_dir)
        stdout_file = os.path.join(namespace.output_dir, 'output.log')
        stderr_file = os.path.join(namespace.output_dir, 'error.log')
    
    daemon = WorkflowDaemon('/tmp/workflow.pid',
                            stdout=stdout_file,
                            stderr=stderr_file,
                            check_frequency=namespace.check_frequency,
                            workflow_recovery=namespace.recover)
    
    if namespace.command == 'start':
        daemon.start()
    elif namespace.command == 'stop':
        daemon.stop()
    elif namespace.command == 'restart':
        daemon.restart()

    sys.exit(0)
