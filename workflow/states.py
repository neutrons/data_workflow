"""
    Action classes to be called when receiving specific messages.
"""
import stomp
from state_utilities import logged_action
from settings import brokers, icat_user, icat_passcode
import logging

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
    
    def send(self, destination, message, persistent='true'):
        """
            Send a message to a queue
            @param destination: name of the queue
            @param message: message content
        """
        conn = stomp.Connection(host_and_ports=brokers, 
                        user=icat_user, passcode=icat_passcode, 
                        wait_on_receipt=True)
        conn.set_listener('workflow_manager', self)
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=message, persistent=persistent)
        # Sometimes the socket gets wiped out before we get a chance to complete
        # disconnecting
        try:
            conn.disconnect()
        except:
            logging.info("Send socket already closed: skipping disconnection")


class Postprocess_data_ready(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Tell workers for start processing
        self.send(destination='/queue/CATALOG.DATA_READY', message=message, persistent='true')
        self.send(destination='/queue/REDUCTION.DATA_READY', message=message, persistent='true')
        
        
class Reduction_complete(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Tell workers to catalog the output
        self.send(destination='/queue/REDUCTION_CATALOG.DATA_READY', message=message, persistent='true')
