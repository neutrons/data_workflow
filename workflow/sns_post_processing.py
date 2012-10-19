#!/usr/bin/env python
from workflow_manager import WorkflowManager
from settings import brokers, icat_user, icat_passcode
from daemon import Daemon
import sys
import os
import argparse

# List of queues to listen to. Each queue must have a
# corresponding class in states.py
queues = ['TRANSLATION.STARTED',
          'TRANSLATION.COMPLETE',
          'POSTPROCESS.DATA_READY',
          'CATALOG.STARTED',
          'CATALOG.COMPLETE',
          'REDUCTION.STARTED',
          'REDUCTION.DISABLED',
          'REDUCTION.COMPLETE',
          'REDUCTION.NOT_NEEDED',
          'REDUCTION_CATALOG.STARTED',
          'REDUCTION_CATALOG.COMPLETE',
          'POSTPROCESS.INFO',
          'POSTPROCESS.ERROR',
          'POSTPROCESS.CHECK']

class WorkflowDaemon(Daemon):
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null',
                 check_frequency=None, workflow_recovery=False, flexible_tasks=False):
        """
            Initialize the daemon's options
            @param pidfile: path to the PID file
            @param stdin: path to use to redirect stdin
            @param stdout: path to use to redirect stdout
            @param stderr: path to use to redirect stderr
            @param check_frequency: number of hours between workflow checks
            @param workflow_recovery: if True, the manager will try to recover from failures
            @param flexible_tasks: if True, the DB will define tasks as oppose to using hard-coded tasks
        """
        super(WorkflowDaemon, self).__init__(pidfile, stdin, stdout, stderr)
        self._check_frequency = check_frequency
        self._workflow_recovery = workflow_recovery
        self._flexible_tasks = flexible_tasks
        
    def run(self):
        """
            Run the workflow manager daemon
        """
        check_frequency = 24
        workflow_check = False
        if self._check_frequency is not None:
            check_frequency = self._check_frequency
            workflow_check = True
            
        mng = WorkflowManager(brokers, icat_user, icat_passcode, queues, 
                              workflow_check=workflow_check,
                              check_frequency=check_frequency,
                              workflow_recovery=self._workflow_recovery,
                              flexible_tasks=self._flexible_tasks)
        mng.processing_loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='SNS data workflow manager')
    
    # Location of the output directory, where we put the output.log and error.log files
    parser.add_argument('-o', metavar='directory',
                        help='location of the output directory',
                        dest='output_dir')
    
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'dump'])
    
    # Workflow verification and recovery options
    parser.add_argument('-f', metavar='hours',
                        help='number of hours between workflow checks',
                        type=int, dest='check_frequency')
    
    parser.add_argument('-r', help='try to recover from workflow problems',
                        action='store_true', dest='recover')
    
    parser.add_argument('--flexible_tasks', help='read task definitions from DB',
                        action='store_true', dest='flexible_tasks')
    
    namespace =  parser.parse_args()
    
    # If we just need to dump the workflow tables,
    # do it and stop here
    if namespace.command == 'dump':
        from database import transactions
        transactions.sql_dump_tasks()
        sys.exit(0)
        
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
                            workflow_recovery=namespace.recover,
                            flexible_tasks=namespace.flexible_tasks)
    
    if namespace.command == 'start':
        daemon.start()
    elif namespace.command == 'stop':
        daemon.stop()
    elif namespace.command == 'restart':
        daemon.restart()

    sys.exit(0)
