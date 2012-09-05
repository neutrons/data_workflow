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
logging.getLogger().setLevel(logging.INFO)


class WorkflowManager(stomp.ConnectionListener):

    def __init__(self, brokers, user, passcode, queues=[]):
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._queues = queues
        ## Delay between loops
        self._delay = 5.0
        self._connection = None
        self._connected = False
    def on_message(self, headers, message):
        """
            Process a message. 
            Example of an ActiveMQ header:
            headers: {'expires': '0', 'timestamp': '1344613053723', '
                  destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}
        """
        destination = headers["destination"].replace('/queue/','')
        destination = destination.replace('.', '_')
        destination = destination.capitalize()
        
        # Find a custom action for this message
        action = None
        if hasattr(states, destination):
            action_cls = getattr(states, destination)
            if action_cls is not None:
                action = action_cls()
                
        # If no custom action was found, use the default
        if action is None:
            action = states.StateAction()
        
        # Execute the appropriate action
        try:
            action(headers, message)
        except:
            type, value, tb = sys.exc_info()
            logging.error("%s: %s" % (type, value))
        
    def on_disconnected(self):
        self._connected = False
        
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
            #from workflow_process import WorkflowProcess
            #wk = WorkflowProcess()
            #wk.verify_workflow()
    
    def processing_loop(self):
        """
            Process events as they happen
        """
        listen = True 
        while(listen):
            try:
                # Get the next message in the post-processing queue
                self.listen_and_wait(self._delay)
            except KeyboardInterrupt:
                listen = False
            finally:
                self._disconnect()
