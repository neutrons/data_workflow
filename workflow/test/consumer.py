"""
    Dummy client to simulate the worker nodes
"""
import time
#import states
import stomp
import sys
import logging
logging.getLogger().setLevel(logging.INFO)

class Consumer(stomp.ConnectionListener):
    def __init__(self, brokers, user, passcode, queues=[]):
        self._delay = 5.0
        self._connection = None
        self._connected = False
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._queues = queues
        ## Delay between loops
        self._delay = 5.0
        self._connection = None
        self._connected = False


    def on_receipt(self, headers, body):
        print "RECEIPT: %s" % headers
        
    def send(self, destination, message, persistent='true'):
        self._connection.send(destination=destination, message=message, persistent=persistent)
        print "  -> %s" % destination
        
    def on_message(self, headers, message):
        print "<--- %s: %s" % (headers["destination"], message)
        gotit = False
        destination = headers["destination"] 
        if destination=='/queue/REDUCTION.DATA_READY':
            self.send('/queue/REDUCTION.STARTED', message, persistent='true')
            self.send('/queue/REDUCTION.COMPLETE', message, persistent='true')
            gotit = True
        elif destination=='/queue/CATALOG.DATA_READY':
            self.send('/queue/CATALOG.STARTED', message, persistent='true')
            self.send('/queue/CATALOG.COMPLETE', message, persistent='true')
            gotit = True
        elif destination=='/queue/REDUCTION_CATALOG.DATA_READY':
            self.send('/queue/REDUCTION_CATALOG.STARTED', message, persistent='true')
            self.send('/queue/REDUCTION_CATALOG.COMPLETE', message, persistent='true')
            gotit = True
        elif destination=='/queue/LIVEDATA.UPDATE':
            print "Live data was updated.  Yeh Haw!"
            gotit=True

        if gotit==True:
            self._connection.ack(headers)

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
        conn.set_listener('worker_bee', self)
        conn.start()
        conn.connect()
        for q in self._queues:
            conn.subscribe(destination=q, ack='client', persistent='true')
        self._connection = conn
        self._connected = True
        logging.info("Connected to %s:%d\n" % conn.get_host_and_port())

    def on_disconnected(self):
        self._connected = False


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
        _listen = True
        conn = None
        while(_listen):
            try:
                # Get the next message in the post-processing queue
                self.listen_and_wait(self._delay)
            except KeyboardInterrupt:
                print "\nStopping"
                _listen = False
            finally:
                self._disconnect()

