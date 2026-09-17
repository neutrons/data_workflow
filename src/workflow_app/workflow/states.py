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

# Validated before being interpolated into a queue name, so that a malformed
# instrument cannot inject queue delimiters ("."), STOMP path segments
# ("/queue/"), or Artemis wildcards ("*", "#"). Underscore is safe and real
# (REF_L, REF_M).
_VALID_INSTRUMENT_RE = re.compile(r"^[a-z0-9_]+$")

# Queue families that split per instrument. CATALOG.ONCAT.DATA_READY is
# deliberately absent: cataloging goes to OnCat, a single external service with
# no per-instrument fairness problem.
_PER_INSTRUMENT_QUEUE_ROOTS = ("REDUCTION", "REDUCTION_CATALOG")


def per_instrument_queue_name(shared_queue, instrument):
    """
    Build the per-instrument name for a queue, or None if that queue does not split::

        REDUCTION.DATA_READY          -> REDUCTION.EQSANS.DATA_READY
        REDUCTION.HIMEM.DATA_READY    -> REDUCTION.HIMEM.EQSANS.DATA_READY
        REDUCTION_CATALOG.DATA_READY  -> REDUCTION_CATALOG.EQSANS.DATA_READY

    Inserting before the last segment keeps a tier segment (HIMEM) next to the
    family root, so the high-memory worker pool keeps its own lane.

    :param shared_queue: queue name as configured today (no /queue/ prefix)
    :param instrument: validated, lowercase instrument name
    :return: per-instrument queue name, or None if this queue is not split
    """
    parts = shared_queue.split(".")
    if len(parts) < 2 or parts[0] not in _PER_INSTRUMENT_QUEUE_ROOTS or parts[-1] != "DATA_READY":
        return None
    return ".".join(parts[:-1] + [instrument.upper(), parts[-1]])


class _RoutingLogThrottle:
    """
    Bound repeated routing log lines: log the first occurrence of a key, then
    every ``every``-th. Without this a message flood, the very scenario this
    feature exists for, would emit one line per message. Count based rather than
    timed so the behavior is deterministic.
    """

    def __init__(self, every=500):
        self._every = every
        self._counts = {}
        self._last_emit = {}

    def record(self, key):
        """Return ``(should_log, suppressed_since_last_emit)`` for this occurrence."""
        count = self._counts.get(key, 0) + 1
        self._counts[key] = count
        if count == 1 or (self._every > 0 and count % self._every == 0):
            suppressed = count - self._last_emit.get(key, 0) - 1
            self._last_emit[key] = count
            return True, max(suppressed, 0)
        return False, 0

    def reset(self):
        """Clear all counters. Safe to call at any time."""
        self._counts.clear()
        self._last_emit.clear()


_routing_log_throttle = _RoutingLogThrottle()


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

        Anything we cannot use (unparseable message, missing field, wrong type,
        unsafe value) returns None so the caller falls back to the shared queue.

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

    def resolve_destination_queue(self, message, shared_queue):
        """
        Choose the destination for a message, honoring the feature flag.

        Returns ``shared_queue`` unchanged unless the flag is on, the message
        carries a usable instrument, and the queue is one that splits. Callers
        therefore never need to know which queues split and which do not.

        The flag is read at call time so it can be toggled per-process.

        :param message: JSON-encoded message content
        :param shared_queue: queue name as configured today
        :return: queue name string
        """
        if not settings.ENABLE_PER_INSTRUMENT_QUEUES:
            return shared_queue

        instrument = self.get_instrument_from_message(message)
        if not instrument:
            self._log_routing_decision(
                logging.WARNING,
                decision="fallback",
                instrument=None,
                queue=shared_queue,
                reason="no_valid_instrument",
            )
            return shared_queue

        queue = per_instrument_queue_name(shared_queue, instrument)
        if queue is None:
            self._log_routing_decision(
                logging.DEBUG,
                decision="shared",
                instrument=instrument,
                queue=shared_queue,
                reason="queue_not_split_per_instrument",
            )
            return shared_queue

        self._log_routing_decision(
            logging.INFO,
            decision="per_instrument",
            instrument=instrument,
            queue=queue,
            reason="ok",
        )
        return queue

    @staticmethod
    def _log_routing_decision(level, decision, instrument, queue, reason):
        """
        Emit one routing-decision line, key=value so monitoring can parse it::

            per_instrument_routing decision=<...> instrument=<...> queue=<...> reason=<...>

        Repeats are rate limited, and a throttled line carries ``suppressed=<n>``.
        """
        should_log, suppressed = _routing_log_throttle.record((decision, queue))
        if not should_log:
            return
        line = "per_instrument_routing decision=%s instrument=%s queue=%s reason=%s" % (
            decision,
            instrument or "none",
            queue,
            reason,
        )
        if suppressed:
            line += " suppressed=%d" % suppressed
        logging.log(level, line)

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
        Run the task definition stored in the database for this instrument.

        This is the path most instruments actually take, so routing is applied to
        the configured task queues here too. Each is resolved on its own, which
        keeps a task that fans out to both REDUCTION.DATA_READY and
        CATALOG.ONCAT.DATA_READY correct.

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
                destination = "/queue/%s" % self.resolve_destination_queue(message, item)
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
        Send a message to a queue.

        A failed send (no connection, or the broker raising) is recorded to
        POSTPROCESS.ERROR with context rather than being dropped, and the
        exception is swallowed so one bad send does not abort the rest of the
        handler.

        :param destination: name of the queue
        :param message: message content
        """
        logging.debug("Send: %s" % destination)
        if self._send_connection is None:
            self._record_send_error(destination, message, "No AMQ connection")
            return
        try:
            self._send_connection.send(destination, message, persistent=persistent)
        except Exception:
            logging.exception("Failed to send message to %s", destination)
            self._record_send_error(destination, message, "Send to broker failed")
            return
        headers = {"destination": destination, "message-id": ""}
        transactions.add_status_entry(headers, message)

    def _record_send_error(self, destination, message, reason):
        """
        Record a POSTPROCESS.ERROR status entry for a message that could not be sent.

        This is the containment path, so it must never raise. The write itself is
        guarded because add_status_entry expects fields like instrument/ipts and
        would raise on a message lacking them, or if the database is down during
        the same outage that broke the send.

        :param destination: the queue we were trying to send to
        :param message: the original message body
        :param reason: short human-readable reason for the failure
        """
        logging.error("%s: could not send to %s", reason, destination)
        headers = {"destination": "/queue/%s" % POSTPROCESS_ERROR, "message-id": ""}
        try:
            data_dict = json.loads(message)
            if not isinstance(data_dict, dict):
                data_dict = {"message": data_dict}
        except (json.JSONDecodeError, TypeError):
            data_dict = {"message": message if isinstance(message, str) else repr(message)}
        data_dict["error"] = "%s: could not send to %s" % (reason, destination)
        try:
            transactions.add_status_entry(headers, json.dumps(data_dict))
        except Exception:
            logging.exception("Failed to record POSTPROCESS.ERROR status entry for %s", destination)


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
        reduction_queue = self.resolve_destination_queue(message, REDUCTION_DATA_READY)

        # Tell workers for start processing. Cataloging stays on the shared queue.
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
    Default action for REDUCTION.REQUEST messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        reduction_queue = self.resolve_destination_queue(message, REDUCTION_DATA_READY)

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
    Default action for REDUCTION.COMPLETE messages
    """

    def __call__(self, headers, message):
        """
        Called to process a message

        :param headers: message headers
        :param message: JSON-encoded message content
        """
        catalog_queue = self.resolve_destination_queue(message, REDUCTION_CATALOG_DATA_READY)

        # Tell workers to catalog the output
        self.send(
            destination="/queue/%s" % catalog_queue,
            message=message,
            persistent="true",
        )
