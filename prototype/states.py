"""
Action classes to be called when receiving specific messages.

To add an action for a specific queue, add a StateAction class
with the name of the queue in lower-case, replacing periods with underscores.
"""

import importlib
import inspect
import json
import logging
import re

from .database import transactions
from .settings import CATALOG_DATA_READY, POSTPROCESS_ERROR, REDUCTION_CATALOG_DATA_READY, REDUCTION_DATA_READY
from .state_utilities import logged_action


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

    def get_instrument_from_message(self, message):
        """
        Extract instrument name from message.

        :param message: JSON-encoded message content
        :return: lowercase instrument name or None
        """
        try:
            data = json.loads(message)
            if "instrument" in data:
                return data["instrument"].lower()
        except (json.JSONDecodeError, KeyError, AttributeError):
            logging.exception("Failed to extract instrument from message")
        return None

    def get_instrument_queue_name(self, instrument, queue_type="reduction"):
        """
        Generate instrument-specific queue name.

        :param instrument: instrument name (e.g., 'eqsans')
        :param queue_type: type of queue ('reduction', 'catalog', etc.)
        :return: queue name string
        """
        instrument_upper = instrument.upper()

        if queue_type == "reduction":
            return f"REDUCTION.{instrument_upper}.DATA_READY"
        elif queue_type == "catalog":
            return f"CATALOG.{instrument_upper}.DATA_READY"
        elif queue_type == "reduction_catalog":
            return f"REDUCTION_CATALOG.{instrument_upper}.DATA_READY"
        else:
            raise ValueError(f"Unknown queue type: {queue_type}")

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

    def _get_class_from_path(self, class_path: str):
        """
        Returns the class given by the class path
        :param class_path: the class, e.g. "module_name.ClassName"
        :return: class or None
        """
        # check that the string is in the format "package_name.module_name.class_name"
        pattern = r"^[a-zA-Z0-9_\.]+\.[a-zA-Z0-9_]+$"
        if not re.match(pattern, class_path):
            logging.error(f"task_class {class_path} does not match pattern module_name.ClassName")
            return None
        module_name, class_name = class_path.rsplit(".", 1)

        # try importing the class
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            if not inspect.isclass(cls):
                raise ValueError
            return cls
        except (ModuleNotFoundError, AttributeError, ValueError):
            logging.error(f"task_class {class_path} cannot be imported")
            return None

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
            action_cls = self._get_class_from_path(task_def["task_class"])
            if action_cls:
                try:
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
    Handler for POSTPROCESS.DATA_READY messages with per-instrument queue routing.
    Routes to instrument-specific queues for isolation, falls back to shared queue.
    """

    ENABLE_PER_INSTRUMENT_QUEUES = True  # Enable per-instrument routing

    def __call__(self, headers, message):
        """
        Route message to instrument-specific or shared reduction queue.

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        instrument = self.get_instrument_from_message(message)

        # Determine catalog and reduction queue destinations
        if self.ENABLE_PER_INSTRUMENT_QUEUES and instrument:
            # Per-instrument routing for queue isolation
            catalog_queue = self.get_instrument_queue_name(instrument, "catalog")
            reduction_queue = self.get_instrument_queue_name(instrument, "reduction")

            logging.info(
                f"Routing {instrument} run to per-instrument queues: "
                f"catalog={catalog_queue}, reduction={reduction_queue}"
            )
        else:
            # Fallback to shared queues
            catalog_queue = CATALOG_DATA_READY
            reduction_queue = REDUCTION_DATA_READY

            if not instrument:
                logging.warning("Could not extract instrument from message, using shared queue")

        # Tell workers to start processing
        self.send(
            destination="/queue/%s" % catalog_queue,
            message=message,
            persistent="true",
        )
        self.send(
            destination="/queue/%s" % reduction_queue,
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
