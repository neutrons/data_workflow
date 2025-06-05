# pylint: disable=bare-except, line-too-long
"""
ActiveMQ listener class for the workflow manager
"""

import logging

import stomp

from . import states


class Listener(stomp.ConnectionListener):
    """
    AMQ listener for the workflow manager
    """

    # AMQ connection to send messages
    _send_connection = None
    # List of brokers
    _brokers = None
    # AMQ user name
    _user = None
    # AMQ passcode
    _passcode = None

    def __init__(self, use_db_tasks=False, auto_ack=True):
        """
        Initialization

        :param use_db_task: if True, a task definition will be looked for in the DB when executing the action
        """
        # If True, the DB will be queried for task definition
        self._use_db_tasks = use_db_tasks
        self._auto_ack = auto_ack

    def set_amq_user(self, brokers, user, passcode):
        """
        Set the ActiveMQ credentials to use when created a new connection
        """
        self._brokers = brokers
        self._user = user
        self._passcode = passcode

    def on_message(self, frame):
        """
        Process a message.
        Example of an ActiveMQ header:
        headers: {'expires': '0', 'timestamp': '1344613053723',
                  'destination': '/queue/POSTPROCESS.DATA_READY',
                  'persistent': 'true', 'priority': '5',
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}

        :param frame: stomp.utils.Frame
        """
        headers = frame.headers
        message = frame.body
        logging.debug("Recv: %s", headers["destination"])

        # Execute the appropriate action
        try:
            connection = self._get_connection()
            action = states.StateAction(connection=connection, use_db_task=self._use_db_tasks)
            action(headers, message)
        except:  # noqa: E722
            logging.exception("Listener failed to process message:")
            logging.error("  Message: %s: %s", headers["destination"], str(message))
        if not self._auto_ack:
            connection.ack(headers["message-id"], headers["subscription"])

    def set_connection(self, connection):
        """
        Set a AMQ connection
        """
        self._send_connection = connection

    def _get_connection(self):
        """
        Create a connection for sending messages, or return the existing
        one if we already created one
        """
        if self._send_connection is None or self._send_connection.is_connected() is False:
            logging.info("[workflow_send_connection] Attempting to connect to ActiveMQ broker")
            conn = stomp.Connection(host_and_ports=self._brokers, keepalive=True)
            conn.connect(self._user, self._passcode, wait=True)
            self._send_connection = conn
        return self._send_connection
