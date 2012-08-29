"""
    Action classes to be called when receiving specific messages.
"""
import stomp
from state_utilities import logged_action
from workflow.settings import *

class StateAction(object):
    """
        Base class for processing messages
    """
    def __init__(self):
        pass

    @logged_action
    def __call__(self, headers, message):
        """
            Called to process a message
        """
        pass
    
    def send(self, destination, message):
        """
            Send a message to a queue
            @param destination: name of the queue
            @param message: message content
        """
        conn = stomp.Connection(host_and_ports=brokers, 
                        user=icat_user, passcode=icat_passcode, 
                        wait_on_receipt=True)
#                        wait_on_receipt=True, version=1.0)
        conn.set_listener('workflow_manager', self)
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=message)
        conn.disconnect()


class Postprocess_data_ready(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Tell workers for start processing
        self.send(destination='/queue/CATALOG.DATA_READY', message=message)
        self.send(destination='/queue/REDUCTION.DATA_READY', message=message)
        
        
class Reduction_complete(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Tell workers to catalog the output
        self.send(destination='/queue/REDUCTION_CATALOG.DATA_READY', message=message)
