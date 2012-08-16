"""
    Action classes to be called when receiving specific messages.
"""
import stomp
import json
import sys
import logging
from database import transactions
from activemq_settings import *

def decode_message(message):
    """
        Decode message and turn it into a dictionnary 
        we can understand.
        
        Messages from STS are expected to be an absolute path
        of the following type:
        
        Old system: /SNS/EQSANS/IPTS-1234/.../EQSANS_5678_event.nxs
        ADARA:      /SNS/EQSANS/IPTS-1234/nexus/EQSANS_5678.nxs.h5
    """
    tokens = message.split('/')
    if len(tokens)<6:
        raise RuntimeError, "Badly formed message from STS\n  %s" % message
    
    # Get the run number
    run_number = 0
    try:
        for i in range(4,len(tokens)):
            if tokens[i].startswith(tokens[2]):
                file_str = tokens[i].replace('_','.')
                file_tokens = file_str.split('.')
                run_number=int(file_tokens[1])
    except:
        raise RuntimeError, "Could not parse run number in %s" % message
    
    # Get ipts number
    try:
        ipts = tokens[3].split('-')[1]
    except:
        logging.error("Could not parse %s: %s" % (tokens[3], sys.exc_value))
        ipts=None
    
    # Create payload for the message
    data = {"instrument": tokens[2],
            "ipts": ipts,
            "run_number": run_number,
            "data_file": message}
    return data


def logged_action(action):
    """
        Decorator used to log a received message before processing it
    """
    def process_function(self, headers, message):
        # See if we have a JSON message
        try:
            data = json.loads(message)
        except:
            data = decode_message(message)
            message = json.dumps(data)
            
        destination = headers["destination"].replace('/queue/','')
        print "%s r%d: %s" % (data["instrument"],
                              data["run_number"],
                              destination)
        transactions.add_status_entry(headers, message)
        return action(self, headers, message)

    return process_function


class StateAction(object):
    """
        Base class for processing messages
    """
    def __init__(self, connection):
        self._connection = connection

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
                        wait_on_receipt=True, version=1.0)
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
