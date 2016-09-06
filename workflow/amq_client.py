#pylint: disable=bare-except, too-many-instance-attributes, too-many-arguments, invalid-name, line-too-long
"""
    ActiveMQ workflow manager client

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2014 Oak Ridge National Laboratory
"""
import sys
import time
import stomp
import logging
import json
import os

from database.transactions import get_message_queues
from workflow_process import WorkflowProcess
try:
    from . import __version__ as version
except:
    version = 'development'

class Client(object):
    """
        ActiveMQ client
        Holds the connection to a broker
    """

    def __init__(self, brokers, user, passcode,
                 queues=None,
                 workflow_check=False,
                 check_frequency=24,
                 workflow_recovery=False,
                 flexible_tasks=False,
                 consumer_name="amq_consumer",
                 auto_ack=True):
        """
            @param brokers: list of brokers we can connect to
            @param user: activemq user
            @param passcode: passcode for activemq user
            @param queues: list of queues to listen to
            @param workflow_check: if True, the workflow will be checked at a given interval
            @param check_frequency: number of hours between workflow checks
            @param workflow_recovery: if True, the manager will try to recover from workflow problems
            @param flexible_tasks: if True, the workflow tasks will be defined by the DB
            @param consumer_name: name of the AMQ listener
            @param auto_ack: if True, AMQ ack will be auotomatic
        """
        # Connection parameters
        self._auto_ack = auto_ack
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._connection = None
        self._consumer_name = consumer_name
        self._queues = queues
        if self._queues is None:
            self._queues = get_message_queues(True)

        ## Delay between workflow check [in seconds]
        self._workflow_check_delay = 60.0*60.0*check_frequency
        self._workflow_check_start = time.time()
        self._workflow_check = workflow_check
        self._workflow_recovery = workflow_recovery
        self._flexible_tasks = flexible_tasks

        ## Listener used for dealing with incoming messages
        self._listener = None

        startup_msg = "Starting Workflow Manager client %s\n" % self._consumer_name
        startup_msg += "  Version: %s\n" % version
        startup_msg += "  User: %s\n" % self._user
        startup_msg += "  DB task definition allowed? %s\n" % str(self._flexible_tasks)
        startup_msg += "  Workflow check enabled? %s\n" % str(self._workflow_check)
        if self._workflow_check:
            startup_msg += "  Time between checks: %s seconds\n" % str(self._workflow_check_delay)
            startup_msg += "  Recovery enabled?    %s\n" % str(self._workflow_recovery)
            if self._workflow_recovery:
                startup_msg += "  Delay since last activity before attempting recovery: %s seconds\n" % str(self._workflow_check_delay)
        logging.info(startup_msg)

    def set_listener(self, listener):
        """
            Set the listener object that will process each
            incoming message.
            @param listener: listener object
        """
        self._listener = listener
        self._connection = self.new_connection()
        self._listener.set_connection(self._connection)

    def get_connection(self, consumer_name=None):
        """
            Get existing connection or create a new one.
        """
        if self._connection is None or not self._connection.is_connected():
            self._disconnect()
            self._connection = self.new_connection(consumer_name)
        return self._connection

    def new_connection(self, consumer_name=None):
        """
            Establish and return a connection to ActiveMQ
            @param consumer_name: name to give the new connection
        """
        if consumer_name is None:
            consumer_name = self._consumer_name
        logging.info("[%s] Connecting to %s", consumer_name, str(self._brokers))
        if stomp.__version__[0]<4:
            conn = stomp.Connection(host_and_ports=self._brokers,
                                    user=self._user,
                                    passcode=self._passcode,
                                    wait_on_receipt=True)
            conn.set_listener(consumer_name, self._listener)
            conn.start()
            conn.connect()
        else:
            conn = stomp.Connection(host_and_ports=self._brokers, keepalive=True)
            conn.set_listener(consumer_name, self._listener)
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
            if self._auto_ack:
                self._connection.subscribe(destination=q, id=i, ack='auto')
            else:
                self._connection.subscribe(destination=q, id=i, ack='client')

    def _disconnect(self):
        """
            Clean disconnect
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None

    def verify_workflow(self):
        """
            Verify that the workflow has completed for all the runs and
            recover if it hasn't
        """
        if self._workflow_check:
            try:
                WorkflowProcess(connection=self._connection,
                                recovery=self._workflow_recovery,
                                allowed_lag=self._workflow_check_delay).verify_workflow()
            except:
                logging.error("Workflow verification failed: %s", sys.exc_value)

    def listen_and_wait(self, waiting_period=1.0):
        """
            Listen for the next message from the brokers.
            This method will simply return once the connection is
            terminated.
            @param waiting_period: sleep time between connection to a broker
        """
        try:
            self.connect()
            self.verify_workflow()
        except:
            logging.error("Problem starting AMQ client: %s", sys.exc_value)

        last_heartbeat = 0
        while True:
            try:
                if self._connection is None or self._connection.is_connected() is False:
                    self.connect()

                time.sleep(waiting_period)

                try:
                    if time.time()-last_heartbeat>5:
                        last_heartbeat = time.time()
                        data_dict = {"src_name": "workflowmgr",
                                     "status": "0",
                                     "pid": str(os.getpid())}
                        message = json.dumps(data_dict)
                        if stomp.__version__[0]<4:
                            self._connection.send(destination="/topic/SNS.COMMON.STATUS.WORKFLOW.0",
                                                  message=message,
                                                  persistent='false')
                        else:
                            self._connection.send("/topic/SNS.COMMON.STATUS.WORKFLOW.0", message,
                                                  persistent='false')
                except:
                    logging.error("Problem sending heartbeat: %s", sys.exc_value)

                # Check for workflow completion
                if time.time()-self._workflow_check_start>self._workflow_check_delay:
                    self.verify_workflow()
                    self._workflow_check_start = time.time()
            except:
                logging.error("Problem connecting to AMQ broker: %s", sys.exc_value)
                time.sleep(5.0)
