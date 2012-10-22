"""
    Unit tests for the workflow manager
    Assumes that ActiveMQ and the DB server is running
"""
import unittest
import stomp
import json
import time

from workflow.database.settings import brokers, icat_user, icat_passcode
from workflow.workflow_manager import WorkflowManager

def send(destination, message, persistent='true'):
    """
        Send a message to a queue
        @param destination: name of the queue
        @param message: message content
    """
    conn = stomp.Connection(host_and_ports=brokers, 
                            user=icat_user, passcode=icat_passcode, 
                            wait_on_receipt=True)
    conn.start()
    conn.connect()
    conn.send(destination=destination, message=message, persistent=persistent)
    conn.disconnect()
    
class Consumer(stomp.ConnectionListener):
    def __init__(self, brokers, user, passcode, queues=[]):
        self._brokers = brokers
        self._user = user
        self._passcode = passcode
        self._connection = None
        self._connected = False
        self._queues = queues
        self._success = False
        self._success_queue = ''

    def on_message(self, headers, message):
        self._success = False
        data_dict = json.loads(message)
        
        if headers["destination"] == self._success_queue \
            and data_dict["data_file"] == "THIS IS A TEST":
            self._success = True
            
        self.disconnect()

    def connect(self):
        """
            Connect to a broker
        """
        # Do a clean disconnect first
        self.disconnect()
        conn = stomp.Connection(host_and_ports=self._brokers,
                                user=self._user,
                                passcode=self._passcode,
                                wait_on_receipt=True)
        conn.set_listener('worker_bee', self)
        conn.start()
        conn.connect()
        for q in self._queues:
            conn.subscribe(destination=q, ack='auto', persistent='true')
        self._connection = conn
        self._connected = True

    def on_disconnected(self):
        self._connected = False

    def disconnect(self):
        """
            Clean disconnect
        """
        if self._connection is not None and self._connection.is_connected():
            self._connection.disconnect()
        self._connection = None
        self._connected = False

    def listen_and_wait(self, waiting_period=0.5, success_queue=''):
        """
            List for the next message from the brokers
            @param waiting_period: sleep time between connection to a broker
        """
        self._success = False
        self._success_queue = success_queue
        self.connect()
        time.sleep(waiting_period)
        self.disconnect()
        
        return self._success
                

class TestWorkflow(unittest.TestCase):
    """
        Test default workflow tasks
    """
    
    def setUp(self):
        data_dict = {"instrument": "HYSA",
             "ipts": "IPTS-%d" % 5678,
             "run_number": 1234,
             "data_file": 'THIS IS A TEST',
             "information": 'THIS IS A TEST: information',
             "error": 'THIS IS A TEST: error'}
        self._data = json.dumps(data_dict)
        
        self.wfmng = WorkflowManager(brokers, icat_user, icat_passcode,
                                     workflow_check=False,
                                     flexible_tasks=True)
        
    def _check_output(self, input_queue, output_queue):
        """
            @param input_queue: input queue that should produce the output_queue
            @param output_queue: output queue used by the workflow manager
        """
        # Set up the test consumer for the two outgoing queues
        c = Consumer(brokers, icat_user, icat_passcode, [output_queue])
        
        # Purge the success queues
        while (c.listen_and_wait(success_queue="/queue/%s" % output_queue)):
            pass
        
        # Send the postprocess data ready message
        send(input_queue, self._data, persistent='true')
        return c.listen_and_wait(success_queue="/queue/%s" % output_queue)

    def test_postprocess_data_ready_catalog(self):
        self.assertTrue(self._check_output("POSTPROCESS.DATA_READY", "CATALOG.DATA_READY"))
        
    def test_postprocess_data_ready_reduction(self):
        self.assertTrue(self._check_output("POSTPROCESS.DATA_READY","REDUCTION.DATA_READY"))
        
    def test_postprocess_data_ready(self):
        self.assertTrue(self._check_output("REDUCTION.COMPLETE","REDUCTION_CATALOG.DATA_READY"))        
        
if __name__ == '__main__':
    unittest.main()