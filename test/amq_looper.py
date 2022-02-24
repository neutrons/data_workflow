# pylint: disable=bare-except, too-many-arguments, invalid-name
"""
    AMQ test client
"""
import sys
import time
import stomp
import json
import settings
from settings import brokers as amq_brokers
from settings import amq_user
from settings import amq_pwd
from settings import queues as amq_queues

import logging
import logging.handlers

logging.getLogger().setLevel(logging.WARN)
# Formatter
ft = logging.Formatter("%(asctime)-15s %(message)s")
# Create a log file handler
fh = logging.handlers.TimedRotatingFileHandler("amq_looper.log", when="midnight", backupCount=15)
fh.setLevel(logging.INFO)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)


# ACK data
acks = {}


class Listener(stomp.ConnectionListener):
    """
    Base listener class for an ActiveMQ client

    A fully implemented class should overload
    the on_message() method to process incoming
    messages.
    """

    _connection = None

    def set_connection(self, connection):
        """
        Set the AMQ connection
        """
        self._connection = connection

    def on_message(self, headers, message):
        """
        Process a message.
        @param headers: message headers
        @param message: JSON-encoded message content
        """
        destination = headers["destination"]
        self._connection.ack(headers["message-id"], headers["subscription"])
        # Load the JSON message into a dictionary
        try:
            data_dict = json.loads(message)
        except:  # noqa: E722
            logging.error("Could not decode message from %s", destination)
            logging.error(sys.exc_value)
            return

        process_ack(data_dict)


def process_ack(data=None):
    """
    Process a ping request ack
    @param data: data that came in with the ack
    """
    try:
        if data is None:
            for proc_name in acks:
                if acks[proc_name] is not None and time.time() - acks[proc_name] > 45:
                    logging.error("Client %s disappeared", proc_name)
                    acks[proc_name] = None
        elif "request_time" in data:
            proc_name = data["src_name"]
            delta_time = time.time() - data["request_time"]
            logging.warning("Delta time: %s", delta_time)
            if delta_time > 60:
                logging.error("Client %s took more than 60 secs to answer", proc_name)
            if proc_name in acks and acks[proc_name] is None:
                logging.error("Client %s reappeared", proc_name)
            acks[proc_name] = time.time()
    except:  # noqa: E722
        logging.error("Error processing ack: %s", sys.exc_value)


class Client(object):
    """
    ActiveMQ client
    Holds the connection to a broker
    """

    def __init__(self, brokers, user, passcode, queues=None, consumer_name="amq_consumer"):
        """
        @param brokers: list of brokers we can connect to
        @param user: activemq user
        @param passcode: passcode for activemq user
        @param queues: list of queues to listen to
        @param consumer_name: name of the AMQ listener
        """
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._connection = None
        self._queues = queues
        self._consumer_name = consumer_name
        self._listener = None

    def set_listener(self, listener):
        """
        Set the listener object that will process each
        incoming message.
        @param listener: listener object
        """
        self._listener = listener
        self._connection = self.get_connection()
        self._listener.set_connection(self._connection)

    def get_connection(self):
        """
        Establish and return a connection to ActiveMQ
        @param listener: listener object
        """
        logging.info("[%s] Connecting to %s", self._consumer_name, str(self._brokers))
        conn = stomp.Connection(host_and_ports=self._brokers)
        conn.set_listener(self._consumer_name, self._listener)
        conn.start()
        conn.connect(self._user, self._passcode, wait=True)
        # Give the connection threads a little breather
        time.sleep(0.5)
        return conn

    def connect(self):
        """
        Connect to a broker
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()

        logging.info("[%s] Subscribing to %s", self._consumer_name, str(self._queues))
        for i, q in enumerate(self._queues):
            self._connection.subscribe(destination=q, id=i, ack="client")

    def _disconnect(self):
        """
        Clean disconnect
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None

    def stop(self):
        """
        Disconnect and stop the client
        """
        self._disconnect()
        if self._connection is not None:
            self._connection.stop()
        self._connection = None

    def listen_and_wait(self):
        """
        Listen for the next message from the brokers.
        This method will simply return once the connection is
        terminated.
        """
        try:
            self.connect()
        except:  # noqa: E722
            logging.error("Problem starting AMQ client: %s", sys.exc_value)

        last_heartbeat = 0
        while True:
            try:
                if self._connection is None or self._connection.is_connected() is False:
                    self.connect()
                try:
                    if time.time() - last_heartbeat > 5:
                        last_heartbeat = time.time()
                        # Send ping request
                        if hasattr(settings, "PING_TOPIC"):
                            from settings import PING_TOPIC, ACK_TOPIC

                            payload = {
                                "reply_to": ACK_TOPIC,
                                "src_name": "looper",
                                "request_time": time.time(),
                            }
                            self.send(PING_TOPIC, json.dumps(payload))
                            process_ack()
                        else:
                            logging.error("settings.PING_TOPIC is not defined")
                except:  # noqa: E722
                    logging.error("Problem writing heartbeat %s", sys.exc_value)
            except:  # noqa: E722
                logging.error("Problem connecting to AMQ broker %s", sys.exc_value)
                time.sleep(5.0)

    def send(self, destination, message, persistent="false"):
        """
        Send a message to a queue
        @param destination: name of the queue
        @param message: message content
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        self._connection.send(destination, message, persistent=persistent)


if __name__ == "__main__":
    logging.warning("Starting")
    client = Client(amq_brokers, amq_user, amq_pwd, amq_queues, "amq_looper")
    listener = Listener()
    client.set_listener(listener)
    client.listen_and_wait()
