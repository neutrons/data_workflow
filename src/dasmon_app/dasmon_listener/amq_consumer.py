# pylint: disable=invalid-name, line-too-long, too-many-locals, bare-except, too-many-statements, too-many-branches
"""
    DASMON ActiveMQ consumer class

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
import sys
import time
import stomp
import logging
import json
import os
import datetime
import smtplib
from email.mime.text import MIMEText

if os.path.isfile("settings.py"):
    logging.warning("Using local settings.py file")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dasmon_listener.settings")

from . import settings  # noqa: E402
from .settings import INSTALLATION_DIR  # noqa: E402
from .settings import PURGE_TIMEOUT  # noqa: E402
from .settings import IMAGE_PURGE_TIMEOUT  # noqa: E402
from .settings import MIN_NOTIFICATION_LEVEL  # noqa: E402

sys.path.append(INSTALLATION_DIR)

import django  # noqa: E402

django.setup()
from django.utils import timezone  # noqa: E402

from reporting.dasmon.models import (  # noqa: E402
    StatusVariable,
    Parameter,
    StatusCache,
    Signal,
    UserNotification,
)  # noqa: E402
from reporting.pvmon.models import (  # noqa: E402
    PV,
    PVCache,
    PVString,
    PVStringCache,
    MonitoredVariable,
)  # noqa: E402
from workflow.database.report.models import Instrument  # noqa: E402


# ACK data
acks = {}

# Extra logs
EXTRA_LOGS = True

# Heartbeat delay [secs]
HEARTBEAT_DELAY = 120

# How often we purge the DB entries
PURGE_DELAY = 600


class Listener(stomp.ConnectionListener):
    """
    Base listener class for an ActiveMQ client

    A fully implemented class should overload
    the on_message() method to process incoming
    messages.
    """

    def __init__(self):
        super().__init__()
        # Get a snapshot of the current set of instruments
        # Turn the QuerySet into a list to ensure that the query
        # is executed now as opposed to every time we need an instrument
        self._instruments = list(Instrument.objects.all())

        # Do the same thing for the list of parameters
        self._parameters = list(Parameter.objects.all())

    def retrieve_parameter(self, key):
        """
        Retrieve of create a Parameter entry
        """
        for key_id in self._parameters:
            if str(key_id) == key:
                return key_id
        # If we haven't found it, create it.
        key_id = Parameter(name=key)
        key_id.save()
        self._parameters.append(key_id)
        return key_id

    def retrieve_instrument(self, instrument_name):
        """
        Retrieve or create an instrument given its name
        """
        # Get or create the instrument object from the DB
        for instrument in self._instruments:
            if str(instrument) == instrument_name:
                return instrument
        # If we haven't found it, create it.
        instrument = Instrument(name=instrument_name)
        instrument.save()
        self._instruments.append(instrument)
        return instrument

    def on_message(self, frame):
        """
        Process a message.
        @param frame: stomp.utils.Frame
        """
        headers = frame.headers
        message = frame.body
        destination = headers["destination"]
        # Load the JSON message into a dictionary
        try:
            data_dict = json.loads(message)
        except:  # noqa: E722
            logging.error("Could not decode message from %s", destination)
            logging.error(sys.exc_info()[1])
            return
        # If we get a STATUS message, store it as such
        if destination.endswith(".ACK"):
            process_ack(data_dict, headers)
            return

        # Extract the instrument name
        instrument = None
        try:
            toks = destination.upper().split(".")
            if len(toks) > 1:
                instrument_name = toks[1].lower()
                # Get the instrument object
                instrument = self.retrieve_instrument(instrument_name)
        except:  # noqa: E722
            logging.error("Could not extract instrument name from %s", destination)
            logging.error(str(sys.exc_info()[1]))
            return

        if "STATUS" in destination:
            # STS is the Streaming Translation Service, also referred to as STC.
            if "STS" in destination:
                key_id = self.retrieve_parameter("system_sts")
                store_and_cache(instrument, key_id, data_dict["status"], cache_only=True)
            elif "STC" in destination:
                key_id = self.retrieve_parameter("system_stc")
                store_and_cache(instrument, key_id, data_dict["status"], cache_only=True)
            elif "SMS" in destination:
                key_id = self.retrieve_parameter("system_sms")
                store_and_cache(instrument, key_id, data_dict["status"], cache_only=True)
            elif "status" in data_dict:
                key = None
                if "src_id" in data_dict:
                    key = "system_%s" % data_dict["src_id"].lower()
                elif "src_name" in data_dict:
                    key = "system_%s" % data_dict["src_name"].lower()
                if key is not None:
                    if key.endswith(".0"):
                        key = key[: len(key) - 2]
                    if key.endswith("_0"):
                        key = key[: len(key) - 2]
                    key_id = self.retrieve_parameter(key)
                    store_and_cache(instrument, key_id, data_dict["status"], cache_only=True)
                    if "pid" in data_dict:
                        key_id = self.retrieve_parameter("%s_pid" % key)
                        store_and_cache(instrument, key_id, data_dict["pid"], cache_only=True)

        # Process signals
        elif "SIGNAL" in destination:
            try:
                logging.warning("SIGNAL: %s: %s", destination, str(data_dict))
                process_signal(instrument, data_dict)
            except:  # noqa: E722
                logging.error("Could not process signal: %s", str(data_dict))
                logging.error(sys.exc_info()[1])

        elif "APP.SMS" in destination:
            process_SMS(instrument, headers, data_dict)
        # For other status messages, store each entry
        else:
            timestamp = None
            # Uncomment the following when the DB has migrated to editable timestamps for AMQ message entries
            # if 'timestamp_micro' in data_dict:
            #    timestamp = data_dict['timestamp_micro']
            # elif 'timestamp' in data_dict:
            #    timestamp = data_dict['timestamp']
            for key in data_dict:
                if key == "monitors" and type(data_dict[key]) == dict:
                    for item in data_dict[key]:
                        # Protect against old API
                        if not type(data_dict[key][item]) == dict:
                            key_id = self.retrieve_parameter("monitor_count_%s" % str(item))
                            store_and_cache(
                                instrument,
                                key_id,
                                data_dict[key][item],
                                timestamp=timestamp,
                                cache_only=False,
                            )
                        else:
                            identifier = None
                            counts = None
                            if "id" in data_dict[key][item]:
                                identifier = data_dict[key][item]["id"]
                            if "counts" in data_dict[key][item]:
                                counts = data_dict[key][item]["counts"]
                            if identifier is not None and counts is not None:
                                parameter_name = "%s_count_%s" % (item, identifier)
                                key_id = self.retrieve_parameter(parameter_name)
                                store_and_cache(
                                    instrument,
                                    key_id,
                                    counts,
                                    timestamp=timestamp,
                                    cache_only=False,
                                )
                else:
                    # For this type of status updates, there's no need to deal with old
                    # messages. Just update the cache for messages older than 1 minute.
                    timestamp_ = float(data_dict["timestamp"]) if "timestamp" in data_dict else time.time()
                    delta_time = time.time() - timestamp_
                    cache_only = delta_time > 60
                    key_id = self.retrieve_parameter(key)
                    store_and_cache(
                        instrument,
                        key_id,
                        data_dict[key],
                        timestamp=timestamp,
                        cache_only=cache_only,
                    )


def send_message(sender, recipients, subject, message):
    """
    Send an email message
    @param sender: email of the sender
    @param recipients: list of recipient emails
    @param subject: subject of the message
    @param message: content of the message
    """
    # If no sender or recipients are defined, do nothing
    if len(sender) == 0 or len(recipients) == 0:
        return
    try:
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = ";".join(recipients)
        s = smtplib.SMTP("localhost")
        s.sendmail(sender, recipients, msg.as_string())
        s.quit()
    except:  # noqa: E722
        logging.error("Could not send message: %s", sys.exc_info()[1])


def process_SMS(instrument_id, headers, data):
    """
    Process SMS process information
    The message content looks like this:

       {u'start_sec': u'1460394343',
        u'src_id': u'SMS_32162',
        u'msg_type': u'2686451712',
        u'facility': u'SNS',
        u'timestamp': u'1460394348',
        u'dest_id': u'',
        u'start_nsec': u'554801929',
        u'instrument': u'BL16B',
        u'reason': u'SMS run stopped',
        u'run_number': u'3014'}

    @param instrument_id: Instrument object
    @param data: data dictionary
    """
    try:
        if "run_number" in data and "msg_type" in data and "reason" in data and "ipts" in data:
            from workflow.database.transactions import add_status_entry

            status_data = {
                "instrument": str(instrument_id),
                "ipts": data["ipts"],
                "information": data["reason"],
                "data_file": "",
                "run_number": data["run_number"],
            }
            add_status_entry(
                {"destination": "SMS", "message-id": headers["message-id"]},
                json.dumps(status_data),
            )
    except:  # noqa: E722
        logging.error("Could not process SMS message: %s", sys.exc_info()[1])


def process_ack(data=None, headers=None):
    """
    Process a ping request ack
    @param data: data that came in with the ack
    """
    try:
        from .settings import ALERT_EMAIL, FROM_EMAIL

        if data is None:
            for proc_name in acks:
                # Start complaining if we missed three heartbeats
                if acks[proc_name] is not None and time.time() - acks[proc_name] > 3.0 * HEARTBEAT_DELAY:
                    logging.error("Client %s disappeared", proc_name)
                    acks[proc_name] = None
                    send_message(
                        sender=FROM_EMAIL,
                        recipients=ALERT_EMAIL,
                        subject="Client %s disappeared" % proc_name,
                        message="An AMQ client disappeared",
                    )
        elif "src_name" in data:
            current_time = time.time()
            msg_time = 0
            if headers is not None:
                msg_time = float(headers.get("timestamp", 0)) / 1000.0
                if msg_time > 0:
                    msg_time = current_time - msg_time

            answer_delay = 0
            if "request_time" in data:
                answer_delay = current_time - data["request_time"]

            proc_name = data["src_name"]
            if "pid" in data:
                proc_name = "%s:%s" % (proc_name, data["pid"])

            # Start complaining if we don't get an answer before half our heartbeat delay
            if "request_time" in data and answer_delay > 0.5 * HEARTBEAT_DELAY:
                logging.error(
                    "Client %s took more than %s secs to answer",
                    proc_name,
                    str(answer_delay),
                )
            if proc_name in acks and acks[proc_name] is None:
                logging.error("Client %s reappeared", proc_name)
                send_message(
                    sender=FROM_EMAIL,
                    recipients=ALERT_EMAIL,
                    subject="Client %s reappeared" % proc_name,
                    message="An AMQ client reappeared",
                )
            acks[proc_name] = time.time()
            if EXTRA_LOGS:
                logging.warning("%s ACK deltas: msg=%s rcv=%s", proc_name, msg_time, answer_delay)
    except:  # noqa: E722
        logging.error("Error processing ack: %s", sys.exc_info()[1])


def notify_users(instrument_id, signal):
    """
    Find users who need to be notified and send them a message
    @param instrument_id: Instrument object
    @param signal: Signal object
    """
    try:
        for item in UserNotification.objects.filter(instruments__in=[instrument_id], registered=True):
            message = "A new alert signal was set on %s\n\n" % str(instrument_id).upper()
            message += "    Name:    %s\n" % signal.name
            message += "    Source:  %s\n" % signal.source
            message += "    Message: %s\n" % signal.message
            message += "    Level:   %s\n" % signal.level
            message += "    Time:    %s\n" % signal.timestamp.ctime()
            send_message(
                sender=item.email,
                recipients=[item.email],
                subject="New alert on %s" % str(instrument_id).upper(),
                message=message,
            )
    except:  # noqa: E722
        logging.error("Failed to notify users: %s", sys.exc_info()[1])


def process_signal(instrument_id, data):
    """
    Process and store signal messages.
    @param instrument_id: Instrument object
    @param data: data dictionary

    Asserted signals look like this:
    {
        "msg_type": "2147483648",
        "src_name": "DASMON.0",
        "timestamp": "1375464085",
        "sig_name": "SID_SVP_HIGH",
        "sig_source": "DAS",
        "sig_message": "SV Pressure too high!",
        "sig_level": "3"
    }

    Retracted signals look like this:
    {
        "msg_type": "2147483649",
        "src_name": "DASMON.0",
        "timestamp": "1375464079",
        "sig_name": "SID_SVP_HIGH"
    }
    """
    # Assert a signal
    if "sig_name" in data:
        # Query the DB to see whether we have the signal asserted
        asserted_sig = (
            Signal.objects.filter(instrument_id=instrument_id, name=data["sig_name"]).order_by("timestamp").reverse()
        )
        if "sig_level" in data:
            level = int(data["sig_level"]) if "sig_level" in data else 0
            message = data["sig_message"] if "sig_message" in data else ""
            source = data["sig_source"] if "sig_source" in data else ""
            timestamp = float(data["timestamp"]) if "timestamp" in data else time.time()
            if time.time() - timestamp > 3600:
                return
            timestamp = datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.get_current_timezone())
            if len(asserted_sig) == 0:
                signal = Signal(
                    instrument_id=instrument_id,
                    name=data["sig_name"],
                    source=source,
                    message=message,
                    level=level,
                    timestamp=timestamp,
                )
                signal.save()
            else:
                signal = asserted_sig[0]
                signal.source = source
                signal.message = message
                signal.level = level
                signal.timestamp = timestamp
                signal.save()
            # Notify users only if it the signal level is greater than our threshold.
            if level >= MIN_NOTIFICATION_LEVEL:
                notify_users(instrument_id, signal)
        # Retract a signal
        else:
            for item in asserted_sig:
                item.delete()


def store_and_cache(instrument_id, key_id, value, timestamp=None, cache_only=False):
    """
    Protected store and cache process.
    Store and cache a DASMON parameter
    @param instrument_id: Instrument object
    @param key_id: key Parameter object
    @param value: value for the given key
    @param cache_only: only update cache
    """
    try:
        store_and_cache_(instrument_id, key_id, value, timestamp=timestamp, cache_only=cache_only)
    except:  # noqa: E722
        logging.error("Could not store %s %s=%s", str(instrument_id), str(key_id), str(value))


def store_and_cache_(instrument_id, key_id, value, timestamp=None, cache_only=False):
    """
    Store and cache a DASMON parameter
    @param instrument_id: Instrument object
    @param key_id: key Parameter object
    @param value: value for the given key
    @param cache_only: only update cache
    """
    # Do bother with parameter that are not monitored
    if key_id.monitored is False:
        return

    # The longest allowable string is 128 characters
    value_string = str(value)
    if len(value_string) > 128:
        value_string = value_string[:128]

    datetime_timestamp = datetime.datetime.fromtimestamp(time.time()).replace(tzinfo=timezone.get_current_timezone())
    if cache_only is False:
        status_entry = StatusVariable(instrument_id=instrument_id, key_id=key_id, value=value_string)
        # Force the timestamp value as needed
        if timestamp is not None:
            try:
                datetime_timestamp = datetime.datetime.fromtimestamp(timestamp).replace(
                    tzinfo=timezone.get_current_timezone()
                )
                status_entry.timestamp = datetime_timestamp
            except:  # noqa: E722
                logging.error("Could not process timestamp [%s]: %s", timestamp, sys.exc_info()[1])
        status_entry.save()
        datetime_timestamp = status_entry.timestamp

    # Update the latest value
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id, key_id=key_id).latest("timestamp")
        last_value.value = value_string
        last_value.timestamp = datetime_timestamp
        last_value.save()
    except:  # noqa: E722
        last_value = StatusCache(
            instrument_id=instrument_id,
            key_id=key_id,
            value=value_string,
            timestamp=datetime_timestamp,
        )
        last_value.save()


class Client:
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
        # Get or create the "common" instrument object from the DB.
        # This dummy instrument is used for heartbeats and central services.
        try:
            self.common_instrument = Instrument.objects.get(name="common")
        except Instrument.DoesNotExist:
            self.common_instrument = Instrument(name="common")
            self.common_instrument.save()
        logging.info("Dasmon Listener client 2.0")

    def set_listener(self, listener):
        """
        Set the listener object that will process each
        incoming message.
        @param listener: listener object
        """
        self._listener = listener

    def get_connection(self, listener=None):
        """
        Establish and return a connection to ActiveMQ
        @param listener: listener object
        """
        if listener is None:
            if self._listener is None:
                listener = Listener()
            else:
                listener = self._listener

        logging.info("[%s] Connecting to %s", self._consumer_name, str(self._brokers))
        conn = stomp.Connection(host_and_ports=self._brokers, keepalive=True)
        conn.set_listener(self._consumer_name, listener)
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
        for q in self._queues:
            self._connection.subscribe(destination=q, id=1, ack="auto")

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

    def listen_and_wait(self, waiting_period=1.0):
        """
        Listen for the next message from the brokers.
        This method will simply return once the connection is
        terminated.
        @param waiting_period: sleep time between connection to a broker
        """

        # Retrieve the Parameter object for our own heartbeat
        try:
            pid_key_id = Parameter.objects.get(name="system_dasmon_listener_pid")
        except:  # noqa: E722
            pid_key_id = Parameter(name="system_dasmon_listener_pid")
            pid_key_id.save()

        last_purge_time = None
        last_heartbeat = 0
        while True:
            try:
                if self._connection is None or self._connection.is_connected() is False:
                    self.connect()
                if last_purge_time is None or time.time() - last_purge_time > PURGE_DELAY:
                    last_purge_time = time.time()
                    # Remove old entries
                    delta_time = datetime.timedelta(days=PURGE_TIMEOUT)
                    cutoff = timezone.now() - delta_time
                    StatusVariable.objects.filter(timestamp__lte=cutoff).delete()
                    # StatusCache.objects.filter(timestamp__lte=cutoff).delete()

                    # Remove old PVMON entries: first, the float values
                    PV.objects.filter(update_time__lte=time.time() - PURGE_TIMEOUT * 24 * 60 * 60).delete()
                    old_entries = PVCache.objects.filter(update_time__lte=time.time() - PURGE_TIMEOUT * 24 * 60 * 60)
                    for item in old_entries:
                        if len(MonitoredVariable.objects.filter(instrument=item.instrument, pv_name=item.name)) == 0:
                            item.delete()
                    # Remove old PVMON entries: second, the string values
                    PVString.objects.filter(update_time__lte=time.time() - PURGE_TIMEOUT * 24 * 60 * 60).delete()
                    old_entries = PVStringCache.objects.filter(
                        update_time__lte=time.time() - PURGE_TIMEOUT * 24 * 60 * 60
                    )
                    for item in old_entries:
                        if len(MonitoredVariable.objects.filter(instrument=item.instrument, pv_name=item.name)) == 0:
                            item.delete()
                    # Remove old images
                    delta_time = datetime.timedelta(days=IMAGE_PURGE_TIMEOUT)
                    cutoff = timezone.now() - delta_time
                time.sleep(waiting_period)
                try:
                    if time.time() - last_heartbeat > HEARTBEAT_DELAY:
                        last_heartbeat = time.time()
                        store_and_cache(self.common_instrument, pid_key_id, str(os.getpid()))
                        # Send ping request
                        if hasattr(settings, "PING_TOPIC"):
                            from .settings import PING_TOPIC, ACK_TOPIC

                            payload = {
                                "reply_to": ACK_TOPIC,
                                "request_time": time.time(),
                            }
                            t0 = time.time()
                            self.send(PING_TOPIC, json.dumps(payload))
                            t = time.time() - t0
                            logging.error("Send time: %s", t)
                            process_ack()
                        else:
                            logging.error("settings.PING_TOPIC is not defined")
                except:  # noqa: E722
                    logging.error("Problem writing heartbeat %s", sys.exc_info()[1])
            except:  # noqa: E722
                logging.error("Problem connecting to AMQ broker %s", sys.exc_info()[1])
                time.sleep(5.0)

    def send(self, destination, message, persistent="false"):
        """
        Send a message to a queue.
        This send method is used for heartbeats and doesn't need AMQ persistent messages.
        @param destination: name of the queue
        @param message: message content
        @param persistent: true, to set persistent header
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        self._connection.send(destination, message, persistent=persistent)
