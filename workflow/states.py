"""
    Action classes to be called when receiving specific messages.
"""
import stomp
from database import transactions
from activemq_settings import *

def logged_action(action):
    """
        Decorator used to log a received message before processing it
    """
    def process_function(self, headers, message):
        transactions.add_status_entry(headers, message)
        return action(self, headers, message)

    return process_function

class StateAction(object):
    """
        Base class for processing messages
    """
    def __init__(self, connection):
        self._connection = connection

    def __call__(self, headers, message):
        """
            Called to process a message
        """
        return NotImplemented
    
    def send(self, destination, message):
        """
            Send a message to a queue
            @param destination: name of the queue
            @param message: message content
        """
        conn = stomp.Connection(host_and_ports=brokers, 
                        user=icat_user, passcode=icat_passcode, 
                        wait_on_receipt=True, version=1.0)
        conn.set_listener('workflow_manager', self)
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=message)
        conn.disconnect()
        
class Postprocess_data_ready(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and tell workers for start processing
        print "Data from STS:", message
        self.send(destination='/queue/CATALOG.DATA_READY', message=message)
        self.send(destination='/queue/REDUCTION.DATA_READY', message=message)
        
class Catalog_started(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "ICAT started", message
        
class Catalog_complete(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "ICAT done", message
        
class Reduction_started(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "Reduction started", message
        
class Reduction_complete(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and tell workers to catalog the output
        self.send(destination='/queue/REDUCTION_CATALOG.DATA_READY', message=message)
        print "Reduction done", message
        
class Reduction_catalog_started(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "Reduction catalog started", message
        
class Reduction_catalog_complete(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "Reduction catalog done", message
        
class Reduction_disabled(StateAction):
    @logged_action
    def __call__(self, headers, message):
        # Log to reporting DB and do nothing
        print "Reduction is disabled", message
        