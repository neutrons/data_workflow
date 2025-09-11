#!/usr/bin/env python
# pylint: disable=invalid-name, line-too-long, too-many-arguments
"""
Workflow manager process
"""

import argparse
import logging
import logging.handlers
import os
import sys

import psutil

from workflow.amq_client import Client
from workflow.amq_listener import Listener

from .database import transactions  # noqa: F401
from .settings import BROKERS, LOGGING_LEVEL, WKFLOW_PASSCODE, WKFLOW_USER

# Set log level
logging.getLogger().setLevel(LOGGING_LEVEL)
logging.getLogger("stomp.py").setLevel(logging.WARNING)

# Formatter
ft = logging.Formatter("%(levelname)s:%(asctime)-15s %(message)s")
# Create a stream handler for stdout
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(ft)
logging.getLogger().addHandler(sh)
# Create a log file handler
fh = logging.handlers.TimedRotatingFileHandler("workflow.log", when="midnight", backupCount=15)
fh.setLevel(LOGGING_LEVEL)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)


def start(check_frequency, workflow_recovery, flexible_tasks):
    """
    Run the workflow manager
    """
    auto_ack = True
    if check_frequency is None:
        check_frequency = 24
        workflow_check = False
    else:
        workflow_check = True

    c = Client(
        BROKERS,
        WKFLOW_USER,
        WKFLOW_PASSCODE,
        workflow_check=workflow_check,
        check_frequency=check_frequency,
        workflow_recovery=workflow_recovery,
        flexible_tasks=flexible_tasks,
        consumer_name="workflow_manager",
        auto_ack=auto_ack,
    )

    listener = Listener(use_db_tasks=flexible_tasks, auto_ack=auto_ack)
    listener.set_amq_user(BROKERS, WKFLOW_USER, WKFLOW_PASSCODE)
    c.set_listener(listener)
    c.listen_and_wait(0.1)


def status():
    # check if running by checking for a process with the name workflowmgr
    me = os.getpid()
    for proc in psutil.process_iter(attrs=["pid", "cmdline"]):
        if proc.info["pid"] == me:
            continue
        cmd = " ".join(proc.info.get("cmdline") or [])
        if ("workflowmgr" in cmd or "sns_post_processing" in cmd) and "start" in cmd:
            logging.info("workflowmgr is running with PID %d", proc.info["pid"])
            sys.exit(0)
    logging.error("workflowmgr is not running")
    sys.exit(1)


def run():
    """
    Interactive run command
    """
    # Start/restart options
    start_parser = argparse.ArgumentParser(add_help=False)

    # Workflow verification and recovery options
    start_parser.add_argument(
        "-f",
        metavar="hours",
        help="number of hours between workflow checks",
        type=int,
        dest="check_frequency",
    )

    start_parser.add_argument(
        "-r",
        help="try to recover from workflow problems",
        action="store_true",
        dest="recover",
    )

    start_parser.add_argument(
        "--skip_flexible_tasks",
        help="read task definitions from DB",
        action="store_true",
        dest="flexible_tasks",
    )

    parser = argparse.ArgumentParser(description="SNS data workflow manager")
    subparsers = parser.add_subparsers(dest="command", help="available sub-commands")

    subparsers.add_parser("start", help="Start workflowmgr [-h for help]", parents=[start_parser])
    subparsers.add_parser("status", help="Show running status of workflowmgr")
    subparsers.add_parser("dump", help="Dump task SQL")
    parser_task = subparsers.add_parser("add_task", help="Add task definition [-h for help]")
    parser_task.add_argument(
        "-i",
        metavar="instrument",
        required=True,
        help="name of the instrument to add the task for",
        dest="instrument",
    )
    parser_task.add_argument(
        "-q",
        metavar="input queue",
        required=True,
        help="name of the input queue that triggers the task",
        dest="input_queue",
    )
    parser_task.add_argument(
        "-c",
        metavar="task class",
        default="",
        help="name of the class to be instantiated and executed",
        dest="task_class",
    )
    parser_task.add_argument(
        "-t",
        metavar="task queues",
        nargs="+",
        help="list of task message queues",
        dest="task_queues",
    )
    parser_task.add_argument(
        "-s",
        metavar="success queues",
        nargs="+",
        help="list of task success message queues",
        dest="success_queues",
    )

    namespace = parser.parse_args()

    # If we just need to dump the workflow tables,
    # do it and stop here
    if namespace.command == "dump":
        transactions.sql_dump_tasks()
        sys.exit(0)
    elif namespace.command == "add_task":
        transactions.add_task(
            instrument=namespace.instrument,
            input_queue=namespace.input_queue,
            task_class=namespace.task_class,
            task_queues=namespace.task_queues,
            success_queues=namespace.success_queues,
        )
        sys.exit(0)

    if namespace.command == "start":
        start(namespace.check_frequency, namespace.recover, not namespace.flexible_tasks)
    elif namespace.command == "status":
        status()


if __name__ == "__main__":
    run()
