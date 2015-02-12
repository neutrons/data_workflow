"""
    DASMON ActiveMQ consumer class
    
    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
import time
import stomp
import logging
import json
import os
import sys
import datetime
import smtplib
from email.mime.text import MIMEText

if os.path.isfile("settings.py"):
    logging.warning("Using local settings.py file")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dasmon_listener.settings")

import settings
from settings import INSTALLATION_DIR
from settings import PURGE_TIMEOUT
from settings import TOPIC_PREFIX
sys.path.append(INSTALLATION_DIR)

import django
if django.VERSION[1]>=7:
    django.setup()
from django.utils import timezone

from dasmon.models import StatusVariable, Parameter, StatusCache, Signal
from pvmon.models import PV, PVCache, PVString, PVStringCache, MonitoredVariable
from report.models import Instrument

# ACK data
acks = {}

class Listener(stomp.ConnectionListener):
    """
        Base listener class for an ActiveMQ client

        A fully implemented class should overload
        the on_message() method to process incoming
        messages.
    """
    def on_message(self, headers, message):
        """
            Process a message.
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        destination = headers["destination"]
        # Load the JSON message into a dictionary
        try:
            data_dict = json.loads(message)
        except:
            logging.error("Could not decode message from %s" % destination)
            logging.error(sys.exc_value)
            return
        
        # If we get a STATUS message, store it as such
        if "ACK" in destination:
            process_ack(data_dict)
            return

        # Extract the instrument name
        instrument = None
        try:
            toks = destination.upper().split('.')
            if len(toks)>1:
                if toks[0]=="/TOPIC/%s" % TOPIC_PREFIX:  
                    instrument_name = toks[1].lower()
                    
                    # Get or create the instrument object from the DB
                    try:
                        instrument = Instrument.objects.get(name=instrument_name)
                    except Instrument.DoesNotExist:
                        instrument = Instrument(name=instrument_name)
                        instrument.save()
            if instrument is None:
                logging.error("Could not extract instrument name from %s" % destination)
                return
        except:
            logging.error("Could not extract instrument name from %s" % destination)
            logging.error(str(sys.exc_value))
            return
            
        if "STATUS" in destination:
            if "STS" in destination:
                store_and_cache(instrument, "system_sts", data_dict["status"])
            elif "status" in data_dict:
                key = None
                if "src_id" in data_dict:
                    key = "system_%s" % data_dict["src_id"].lower()
                elif "src_name" in data_dict:
                    key = "system_%s" % data_dict["src_name"].lower()
                if key is not None:
                    if key.endswith(".0"):
                        key = key[:len(key)-2]
                    if key.endswith("_0"):
                        key = key[:len(key)-2]
                    store_and_cache(instrument, key, data_dict["status"])
                    if "pid" in data_dict:
                        store_and_cache(instrument, "%s_pid" % key, data_dict["pid"])

        # Process signals
        elif "SIGNAL" in destination:
            try:
                logging.warn("SIGNAL: %s: %s" % (destination, str(data_dict)))
                process_signal(instrument, data_dict)
            except:
                logging.error("Could not process signal: %s" % str(data_dict))
                logging.error(sys.exc_value)
            
        # For other status messages, store each entry
        else:      
            for key in data_dict:
                if key=='monitors' and type(data_dict[key])==dict:
                    for item in data_dict[key]:
                        # Protect against old API
                        if not type(data_dict[key][item])==dict:
                            store_and_cache(instrument, 'monitor_count_%s' % str(item), data_dict[key][item])
                        else:
                            identifier = None
                            counts = None
                            if "id" in data_dict[key][item]:
                                identifier = data_dict[key][item]["id"]
                            if "counts" in data_dict[key][item]:
                                counts = data_dict[key][item]["counts"]
                            if identifier is not None and counts is not None:
                                parameter_name = "%s_count_%s" % (item, identifier)
                                store_and_cache(instrument, parameter_name, counts)
                else:
                    store_and_cache(instrument, key, data_dict[key])
            
def process_ack(data=None):
    """
        Process a ping request ack
        @param data: data that came in with the ack
    """
    timeout = 15
    try:
        if data is None:
            for proc_name in acks:
                if acks[proc_name] is not None and time.time()-acks[proc_name]>timeout:
                    logging.error("Client %s disappeared" % proc_name)
                    from settings import ALERT_EMAIL
                    acks[proc_name] = None
                    msg = MIMEText("An AMQ client disappeared")
                    msg['Subject'] = "Client %s disappeared" % proc_name
                    msg['From'] = ALERT_EMAIL
                    msg['To'] = ALERT_EMAIL
                    s = smtplib.SMTP('localhost')
                    s.sendmail(ALERT_EMAIL, [ALERT_EMAIL], msg.as_string())
                    s.quit()
        elif 'src_name' in data:
            proc_name = data['src_name']
            if 'pid' in data:
                proc_name = '%s:%s' % (proc_name, data['pid'])
            if 'request_time' in data and time.time()-data['request_time']>10:
                logging.error("Client %s took more than 10 secs to answer" % proc_name)
            if proc_name in acks and acks[proc_name] is None:
                logging.error("Client %s reappeared" % proc_name)
            acks[proc_name] = time.time()
    except:
        logging.error("Error processing ack: %s" % sys.exc_value)

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
    if 'sig_name' in data:
        # Query the DB to see whether we have the signal asserted
        asserted_sig = Signal.objects.filter(instrument_id=instrument_id,
                                             name=data['sig_name']).order_by('timestamp').reverse()
        if 'sig_level' in data:
            level = int(data['sig_level']) if 'sig_level' in data else 0
            message = data['sig_message'] if 'sig_message' in data else ''
            source = data['sig_source'] if 'sig_source' in data else ''
            timestamp = float(data['timestamp']) if 'timestamp' in data else time.time()
            if time.time()-timestamp>3600:
                return
            timestamp = datetime.datetime.fromtimestamp(timestamp).replace(tzinfo=timezone.get_current_timezone())
            if len(asserted_sig) == 0:
                signal = Signal(instrument_id=instrument_id,
                             name=data['sig_name'],
                             source=source,
                             message=message,
                             level=level,
                             timestamp=timestamp)
                signal.save()
            else:
                signal = asserted_sig[0]
                signal.source = source
                signal.message = message
                signal.level = level
                signal.timestamp = timestamp
                signal.save()
    
        # Retract a signal
        else:
            for item in asserted_sig:
                item.delete()
    
    
def store_and_cache(instrument_id, key, value):
    """
        Store and cache a DASMON parameter
        @param instrument_id: Instrument object
        @param key: key string
        @param value: value for the given key
    """
    try:
        key_id = Parameter.objects.get(name=key)
    except:
        key_id = Parameter(name=key)
        key_id.save()
        
    # Do bother with parameter that are not monitored
    if key_id.monitored is False:
        return
    
    # The longest allowable string is 128 characters
    value_string = str(value)
    if len(value_string)>128:
        value_string = value_string[:128]
    status_entry = StatusVariable(instrument_id=instrument_id,
                                  key_id=key_id,
                                  value=value_string)
    status_entry.save()
    
    # Update the latest value
    try:
        last_value = StatusCache.objects.filter(instrument_id=instrument_id,
                                             key_id=key_id).latest('timestamp')
        last_value.value = status_entry.value
        last_value.timestamp = status_entry.timestamp
        last_value.save()
    except:
        last_value = StatusCache(instrument_id=instrument_id,
                                 key_id=key_id,
                                 value=status_entry.value,
                                 timestamp=status_entry.timestamp)
        last_value.save()
    

class Client(object):
    """
        ActiveMQ client
        Holds the connection to a broker
    """
    
    def __init__(self, brokers, user, passcode, 
                 queues=None, consumer_name="amq_consumer"):
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

        logging.info("[%s] Connecting to %s" % (self._consumer_name, str(self._brokers)))
        if stomp.__version__[0]<4:
            conn = stomp.Connection(host_and_ports=self._brokers, 
                                    user=self._user,
                                    passcode=self._passcode, 
                                    wait_on_receipt=True)
            conn.set_listener(self._consumer_name, listener)
            conn.start()
            conn.connect()
        else:
            conn = stomp.Connection(host_and_ports=self._brokers, keepalive=True)
            conn.set_listener(self._consumer_name, listener)
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
        
        logging.info("[%s] Subscribing to %s" % (self._consumer_name,
                                                 str(self._queues)))
        for q in self._queues:
            self._connection.subscribe(destination=q, id=1, ack='auto')
    
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
        # Get or create the "common" instrument object from the DB.
        # This dummy instrument is used for heartbeats and central services.
        try:
            common_instrument = Instrument.objects.get(name='common')
        except Instrument.DoesNotExist:
            common_instrument = Instrument(name='common')
            common_instrument.save()
            
        last_purge_time = None
        last_heartbeat = 0
        while(True):
            try:
                if self._connection is None or self._connection.is_connected() is False:
                    self.connect()
                if last_purge_time is None or time.time()-last_purge_time>120:
                    last_purge_time = time.time()
                    # Remove old entries
                    delta_time = datetime.timedelta(days=PURGE_TIMEOUT)
                    cutoff = timezone.now()-delta_time
                    StatusVariable.objects.filter(timestamp__lte=cutoff).delete()
                    StatusCache.objects.filter(timestamp__lte=cutoff).delete()
                    
                    # Remove old PVMON entries: first, the float values
                    PV.objects.filter(update_time__lte=time.time()-PURGE_TIMEOUT*24*60*60).delete()
                    old_entries = PVCache.objects.filter(update_time__lte=time.time()-PURGE_TIMEOUT*24*60*60)
                    for item in old_entries:
                        if len(MonitoredVariable.objects.filter(instrument=item.instrument,
                                                                pv_name=item.name))==0:
                            item.delete()
                    # Remove old PVMON entries: second, the string values
                    PVString.objects.filter(update_time__lte=time.time()-PURGE_TIMEOUT*24*60*60).delete()
                    old_entries = PVStringCache.objects.filter(update_time__lte=time.time()-PURGE_TIMEOUT*24*60*60)
                    for item in old_entries:
                        if len(MonitoredVariable.objects.filter(instrument=item.instrument,
                                                                pv_name=item.name))==0:
                            item.delete()
                time.sleep(waiting_period)
                try:
                    if time.time()-last_heartbeat>5:
                        last_heartbeat = time.time()
                        store_and_cache(common_instrument, "system_dasmon_listener_pid", str(os.getpid()))
                        # Send ping request
                        if hasattr(settings, "PING_TOPIC"):
                            from settings import PING_TOPIC, ACK_TOPIC
                            payload = {"reply_to": ACK_TOPIC,
                                       "request_time": time.time()}
                            self.send(PING_TOPIC, json.dumps(payload))
                            process_ack()
                        else:
                            logging.error("settings.PING_TOPIC is not defined")
                except:
                    logging.error("Problem writing heartbeat %s" % sys.exc_value)
            except:
                logging.error("Problem connecting to AMQ broker %s" % sys.exc_value)
                time.sleep(5.0)
            
    def send(self, destination, message, persistent='true'):
        """
            Send a message to a queue
            @param destination: name of the queue
            @param message: message content
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.get_connection()
        if stomp.__version__[0]<4:
            self._connection.send(destination=destination, message=message, persistent=persistent)
        else:
            self._connection.send(destination, message, persistent=persistent)
