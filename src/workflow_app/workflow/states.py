"""
    Action classes to be called when receiving specific messages.

    To add an action for a specific queue, add a StateAction class
    with the name of the queue in lower-case, replacing periods with underscores.
"""

from .state_utilities import logged_action
from .settings import POSTPROCESS_ERROR, CATALOG_DATA_READY
from .settings import REDUCTION_DATA_READY, REDUCTION_CATALOG_DATA_READY
from .database import transactions
import json
import logging


class StateAction:
    """
    Base class for processing messages
    """

    _send_connection = None

    def __init__(self, connection=None, use_db_task=False):
        """
        Initialization

        :param connection: AMQ connection to use to send messages
        :param use_db_task: if True, a task definition will be looked for in the DB when executing the action
        """
        self._user_db_task = use_db_task
        self._send_connection = connection

    def _call_default_task(self, headers, message):
        """
        Find a default task for the given message header

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Convert the message queue name into a class name
        destination = headers["destination"].replace("/queue/", "")
        destination = destination.replace(".", "_")
        destination = destination.capitalize()

        # Find a custom action for this message
        if destination in globals():
            action_cls = globals()[destination]
            action_cls(connection=self._send_connection)(headers, message)

    def _call_db_task(self, task_data, headers, message):
        """
        :param task_data: JSON-encoded task definition
        :param headers: message headers
        :param message: JSON-encoded message content
        """
        task_def = json.loads(task_data)
        if (
            "task_class" in task_def
            and (task_def["task_class"] is not None)
            and len(task_def["task_class"].strip()) > 0
        ):
            try:
                toks = task_def["task_class"].strip().split(".")
                module = ".".join(toks[: len(toks) - 1])
                cls = toks[len(toks) - 1]
                exec("from %s import %s as action_cls" % (module, cls))
                action_cls(connection=self._send_connection)(headers, message)  # noqa: F821
            except:  # noqa: E722
                logging.exception("Task [%s] failed:", headers["destination"])
        if "task_queues" in task_def:
            for item in task_def["task_queues"]:
                destination = "/queue/%s" % item
                self.send(destination=destination, message=message, persistent="true")

                headers = {"destination": destination, "message-id": ""}

    @logged_action
    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Find task definition in DB if available
        if self._user_db_task:
            task_data = transactions.get_task(headers, message)
            if task_data is not None:
                self._call_db_task(task_data, headers, message)
                return

        # If we made it here we need to use default tasks
        self._call_default_task(headers, message)

    def send(self, destination, message, persistent="true"):
        """
        Send a message to a queue

        :param destination: name of the queue
        :param message: message content
        """
        logging.debug("Send: %s" % destination)
        if self._send_connection is not None:
            self._send_connection.send(destination, message, persistent=persistent)
            headers = {"destination": destination, "message-id": ""}
            transactions.add_status_entry(headers, message)
        else:
            logging.error("No AMQ connection to send to %s" % destination)
            headers = {"destination": "/queue/%s" % POSTPROCESS_ERROR, "message-id": ""}
            data_dict = json.loads(message)
            data_dict["error"] = "No AMQ connection: Could not send to %s" % destination
            message = json.dumps(data_dict)
            transactions.add_status_entry(headers, message)


class Postprocess_data_ready(StateAction):
    """
    Default action for POSTPROCESS.DATA_READY messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Tell workers for start processing
        self.send(
            destination="/queue/%s" % CATALOG_DATA_READY,
            message=message,
            persistent="true",
        )
        self.send(
            destination="/queue/%s" % REDUCTION_DATA_READY,
            message=message,
            persistent="true",
        )


class Reduction_request(StateAction):
    """
    Default action for REDUCTION.REQUEST messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Tell workers for start reduction
        self.send(
            destination="/queue/%s" % REDUCTION_DATA_READY,
            message=message,
            persistent="true",
        )


class Catalog_request(StateAction):
    """
    Default action for CATALOG.REQUEST messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Tell workers for start cataloging
        self.send(
            destination="/queue/%s" % CATALOG_DATA_READY,
            message=message,
            persistent="true",
        )


class Reduction_complete(StateAction):
    """
    Default action for REDUCTION.COMPLETE messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        # Tell workers to catalog the output
        self.send(
            destination="/queue/%s" % REDUCTION_CATALOG_DATA_READY,
            message=message,
            persistent="true",
        )
