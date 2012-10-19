"""
    Basic workflow manager. The workflow manager will listen to
    a set of queues and reconnect after it has processed a message or
    after it has lost connection.
"""
import time
import states
import stomp
import sys
import logging

# Set log level
logging.getLogger().setLevel(logging.INFO)
# Formatter
ft = logging.Formatter('%(asctime)-15s %(message)s')
# Create a log file handler
fh = logging.FileHandler('workflow.log')
fh.setLevel(logging.INFO)
fh.setFormatter(ft)
logging.getLogger().addHandler(fh)

from workflow_process import WorkflowProcess

class WorkflowManager(stomp.ConnectionListener):

    def __init__(self, brokers, user, passcode, queues=[], workflow_check=False,
                 check_frequency=24, workflow_recovery=False,
                 flexible_tasks=False):
        """
            Start a workflow manager. 
            If flexible_tasks is True, the definition of the actions to be taken
            in response to a given message will be defined in the DB in the Task table.
            Otherwise, the hard-coded actions will be used and the tasks defined in 
            the DB will be ignored.
            
            @param brokers: list of brokers we can connect to
            @param user: activemq user
            @param passcode: passcode for activemq user
            @param queues: list of queues to listen to
            @param workflow_check: if True, the workflow will be checked at a given interval
            @param check_frequency: number of hours between workflow checks
            @param workflow_recovery: if True, the manager will try to recover from workflow problems
            @param flexible_tasks: if True, the workflow tasks will be defined by the DB
        """
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._queues = queues
        ## Delay between loops
        self._delay = 5.0
        ## Delay between workflow check [in seconds]
        self._workflow_check_delay = 60.0*60.0*check_frequency
        self._workflow_check_start = time.time()
        self._workflow_check = workflow_check
        self._workflow_recovery = workflow_recovery
        self._connection = None
        self._connected = False
        self._flexible_tasks = flexible_tasks
        
    def on_message(self, headers, message):
        """
            Process a message. 
            Example of an ActiveMQ header:
            headers: {'expires': '0', 'timestamp': '1344613053723', '
                  destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}

            @param headers: message headers
            @param message: JSON-encoded message content
        """
        # Acknowledge message
        # self._connection.ack(headers)
        
        # Execute the appropriate action
        try:
            action = states.StateAction(use_db_task=self._flexible_tasks)
            action(headers, message)
        except:
            type, value, tb = sys.exc_info()
            logging.error("%s: %s" % (type, value))
        
    def on_disconnected(self):
        self._connected = False
        
    def verify_workflow(self):
        if self._workflow_check:
            try:
                WorkflowProcess(recovery=self._workflow_recovery,
                                allowed_lag=self._workflow_check_delay).verify_workflow()
            except:
                logging.error("Workflow verification failed: %s" % sys.exc_value)
        
    def connect(self):
        """
            Connect to a broker
        """
        # Do a clean disconnect first
        self._disconnect()
        
        conn = stomp.Connection(host_and_ports=self._brokers, 
                                user=self._user,
                                passcode=self._passcode, 
                                wait_on_receipt=True)
        conn.set_listener('workflow_manager', self)
        conn.start()
        conn.connect()
        for q in self._queues:
            conn.subscribe(destination=q, ack='auto', persistent='true')
        self._connection = conn
        self._connected = True
        logging.info("Connected to %s:%d\n" % conn.get_host_and_port())
    
    def _disconnect(self):
        """
            Clean disconnect
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        
    def listen_and_wait(self, waiting_period=1.0):
        """
            List for the next message from the brokers
            @param waiting_period: sleep time between connection to a broker
        """
        self.connect()
        while(self._connected):
            time.sleep(waiting_period)
            
            # Check for workflow completion
            if time.time()-self._workflow_check_start>self._workflow_check_delay:
                self.verify_workflow()
                self._workflow_check_start = time.time()
    
    def processing_loop(self):
        """
            Process events as they happen
        """
        # Check workflow completion
        self.verify_workflow()
        listen = True 
        while(listen):
            try:
                # Get the next message in the post-processing queue
                self.listen_and_wait(self._delay)
            except KeyboardInterrupt:
                listen = False
            finally:
                self._disconnect()
