#!/usr/bin/env python
# pylint: disable=invalid-name, line-too-long, too-many-arguments
"""
    Workflow manager process
"""
import os
import sys
import argparse
import logging
from multiprocessing import Process
from .amq_client import Client
from .amq_listener import Listener
from .settings import brokers


# Backward compatibility protection
from . import settings
if hasattr(settings, 'wkflow_user') and hasattr(settings, 'wkflow_passcode'):
    from .settings import wkflow_user, wkflow_passcode
else:
    from .settings import icat_user as wkflow_user
    from .settings import icat_passcode as wkflow_passcode

from .settings import LOGGING_LEVEL  # noqa: F401
from .daemon import Daemon  # noqa: F401
from .database import transactions  # noqa: F401

# Set log level
logging.getLogger().setLevel(LOGGING_LEVEL)
logging.getLogger('stomp.py').setLevel(logging.WARNING)

# Formatter
ft = logging.Formatter('%(levelname)s:%(asctime)-15s %(message)s')
# Create a log file handler
fh = logging.handlers.TimedRotatingFileHandler('workflow.log', when='midnight', backupCount=15)
fh.setLevel(LOGGING_LEVEL)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)


class WorkflowDaemon(Daemon):
    """
        Workflow daemon
    """

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
        auto_ack = True
        if self._check_frequency is not None:
            check_frequency = self._check_frequency
            workflow_check = True

        c = Client(brokers, wkflow_user, wkflow_passcode,
                   workflow_check=workflow_check,
                   check_frequency=check_frequency,
                   workflow_recovery=self._workflow_recovery,
                   flexible_tasks=self._flexible_tasks,
                   consumer_name="workflow_manager_%s" % self.pidfile,
                   auto_ack=auto_ack)

        listener = Listener(use_db_tasks=self._flexible_tasks, auto_ack=auto_ack)
        listener.set_amq_user(brokers, wkflow_user, wkflow_passcode)
        c.set_listener(listener)
        c.listen_and_wait(0.1)


def run_daemon(pid_file, stdout_file, stderr_file, check_frequency, recover, flexible_tasks, command):
    """
        Start daemon
    """
    daemon = WorkflowDaemon(pid_file,
                            stdout=stdout_file,
                            stderr=stderr_file,
                            check_frequency=check_frequency,
                            workflow_recovery=recover,
                            flexible_tasks=flexible_tasks)
    if command == 'start':
        daemon.start()
    elif command == 'stop':
        daemon.stop()
    elif command == 'restart':
        daemon.restart()


def run():
    """
        Interactive run command
    """
    # Start/restart options
    start_parser = argparse.ArgumentParser(add_help=False)

    # Location of the output directory, where we put the output.log and error.log files
    start_parser.add_argument('-o', metavar='directory',
                              help='location of the output directory',
                              dest='output_dir')

    # Workflow verification and recovery options
    start_parser.add_argument('-f', metavar='hours',
                              help='number of hours between workflow checks',
                              type=int, dest='check_frequency')

    start_parser.add_argument('-r', help='try to recover from workflow problems',
                              action='store_true', dest='recover')

    start_parser.add_argument('--skip_flexible_tasks', help='read task definitions from DB',
                              action='store_true', dest='flexible_tasks')

    parser = argparse.ArgumentParser(description='SNS data workflow manager')
    subparsers = parser.add_subparsers(dest='command', help='available sub-commands')

    subparsers.add_parser('start', help='Start daemon [-h for help]', parents=[start_parser])
    subparsers.add_parser('restart', help='Restart daemon [-h for help]', parents=[start_parser])
    subparsers.add_parser('stop', help='Stop daemon')
    subparsers.add_parser('dump', help='Dump task SQL')
    parser_task = subparsers.add_parser('add_task', help='Add task definition [-h for help]')
    parser_task.add_argument('-i', metavar='instrument', required=True,
                             help='name of the instrument to add the task for',
                             dest='instrument')
    parser_task.add_argument('-q', metavar='input queue', required=True,
                             help='name of the input queue that triggers the task',
                             dest='input_queue')
    parser_task.add_argument('-c', metavar='task class', default='',
                             help='name of the class to be instantiated and executed',
                             dest='task_class')
    parser_task.add_argument('-t', metavar='task queues', nargs='+',
                             help='list of task message queues',
                             dest='task_queues')
    parser_task.add_argument('-s', metavar='success queues', nargs='+',
                             help='list of task success message queues',
                             dest='success_queues')

    namespace = parser.parse_args()

    # If we just need to dump the workflow tables,
    # do it and stop here
    if namespace.command == 'dump':
        transactions.sql_dump_tasks()
        sys.exit(0)
    elif namespace.command == 'add_task':
        transactions.add_task(instrument=namespace.instrument,
                              input_queue=namespace.input_queue,
                              task_class=namespace.task_class,
                              task_queues=namespace.task_queues,
                              success_queues=namespace.success_queues)
        sys.exit(0)

    stdout_file = None
    stderr_file = None
    check_frequency = None
    recover = False
    flexible_tasks = True

    if namespace.command in ['start', 'restart']:
        if namespace.output_dir is not None:
            if not os.path.isdir(namespace.output_dir):
                os.makedirs(namespace.output_dir)
            stdout_file = os.path.join(namespace.output_dir, 'output.log')
            stderr_file = os.path.join(namespace.output_dir, 'error.log')
        if namespace.check_frequency is not None:
            check_frequency = namespace.check_frequency
        if namespace.recover is not None:
            recover = namespace.recover
        if namespace.flexible_tasks is not None:
            flexible_tasks = not namespace.flexible_tasks

    number_of_processes = 1
    if number_of_processes == 1:
        run_daemon('/tmp/workflow.pid', stdout_file, stderr_file,
                   check_frequency,
                   recover,
                   flexible_tasks,
                   namespace.command)
    else:
        for i in range(number_of_processes):
            p = Process(target=run_daemon, args=('/tmp/workflow%d.pid' % i, stdout_file, stderr_file,
                                                 check_frequency,
                                                 recover,
                                                 flexible_tasks,
                                                 namespace.command))
            p.start()
            p.join()

    sys.exit(0)


if __name__ == "__main__":
    run()
