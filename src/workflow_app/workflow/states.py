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

from . import settings
from .database import transactions
from .settings import CATALOG_DATA_READY, POSTPROCESS_ERROR, REDUCTION_CATALOG_DATA_READY, REDUCTION_DATA_READY
from .state_utilities import logged_action

# Instrument names are short alphanumeric tokens (e.g. "eqsans", "cg2", "hb2c").
# Validate strictly before interpolating into a queue name so that a malformed or
# hostile "instrument" value cannot inject queue delimiters ("."), STOMP path
# segments ("/queue/"), or ActiveMQ Artemis wildcard characters ("*", "#").
_VALID_INSTRUMENT_RE = re.compile(r"^[a-z0-9]+$")


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
        Extract and validate the instrument name from a message.

        Returns the lowercase instrument name only when the message is valid JSON,
        carries a string ``instrument`` field, and that field is a plain
        alphanumeric token. Any other case (unparseable message, missing field,
        wrong type, or a value containing characters that are unsafe in a queue
        name) returns ``None`` so the caller falls back to the shared queue.

        :param message: JSON-encoded message content
        :return: lowercase instrument name, or None
        """
        try:
            data = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            logging.debug("Could not parse message as JSON while extracting instrument")
            return None

        if not isinstance(data, dict):
            return None

        instrument = data.get("instrument")
        if not isinstance(instrument, str):
            return None

        instrument = instrument.strip().lower()
        if not _VALID_INSTRUMENT_RE.match(instrument):
            logging.debug("Ignoring invalid instrument value %r for per-instrument routing", instrument)
            return None

        return instrument

    def get_instrument_queue_name(self, instrument, queue_type="reduction"):
        """
        Generate an instrument-specific queue name.

        :param instrument: validated instrument name (e.g. 'eqsans')
        :param queue_type: one of 'reduction', 'reduction_catalog', 'catalog'
        :return: queue name string
        :raises ValueError: if queue_type is unknown
        """
        instrument_upper = instrument.upper()

        if queue_type == "reduction":
            return f"REDUCTION.{instrument_upper}.DATA_READY"
        elif queue_type == "reduction_catalog":
            return f"REDUCTION_CATALOG.{instrument_upper}.DATA_READY"
        elif queue_type == "catalog":
            return f"CATALOG.{instrument_upper}.DATA_READY"
        else:
            raise ValueError(f"Unknown queue type: {queue_type}")

    def resolve_reduction_queue(self, message, shared_queue, queue_type):
        """
        Choose the destination queue for a message, honoring the feature flag.

        When per-instrument routing is enabled (see
        ``settings.ENABLE_PER_INSTRUMENT_QUEUES``) and a valid instrument can be
        extracted, returns the instrument-specific queue name. Otherwise returns
        ``shared_queue`` -- and, if routing is enabled but the instrument is
        missing or invalid, logs a warning so the fallback is visible.

        The flag is read from the settings module at call time so it can be
        toggled per-process (and overridden in tests) without re-importing.

        :param message: JSON-encoded message content
        :param shared_queue: queue name to fall back to
        :param queue_type: queue type passed to get_instrument_queue_name
        :return: queue name string
        """
        if not settings.ENABLE_PER_INSTRUMENT_QUEUES:
            return shared_queue

        instrument = self.get_instrument_from_message(message)
        if not instrument:
            logging.warning(
                "Per-instrument routing enabled but no valid instrument in message; falling back to shared queue %s",
                shared_queue,
            )
            return shared_queue

        queue = self.get_instrument_queue_name(instrument, queue_type)
        logging.info("Routing %s message to per-instrument queue %s", instrument, queue)
        return queue

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
    Default action for POSTPROCESS.DATA_READY messages.

    Routes the reduction message to the instrument-specific REDUCTION queue when
    per-instrument routing is enabled, falling back to the shared queue otherwise.
    The CATALOG message always uses the shared queue (CATALOG.ONCAT.DATA_READY).
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        reduction_queue = self.resolve_reduction_queue(message, REDUCTION_DATA_READY, "reduction")

        # Tell workers for start processing.
        # Cataloging stays on the shared queue for now.
        self.send(
            destination="/queue/%s" % CATALOG_DATA_READY,
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
    Default action for REDUCTION.REQUEST messages.

    Routes to the instrument-specific REDUCTION queue when per-instrument routing
    is enabled, falling back to the shared queue otherwise.
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        reduction_queue = self.resolve_reduction_queue(message, REDUCTION_DATA_READY, "reduction")

        # Tell workers for start reduction
        self.send(
            destination="/queue/%s" % reduction_queue,
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
    Default action for REDUCTION.COMPLETE messages.

    Routes to the instrument-specific REDUCTION_CATALOG queue when per-instrument
    routing is enabled, falling back to the shared queue otherwise.
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        catalog_queue = self.resolve_reduction_queue(message, REDUCTION_CATALOG_DATA_READY, "reduction_catalog")

        # Tell workers to catalog the output
        self.send(
            destination="/queue/%s" % catalog_queue,
            message=message,
            persistent="true",
        )
