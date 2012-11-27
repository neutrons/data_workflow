"""
    Action classes to be called when receiving specific messages.
"""
import stomp
from state_utilities import logged_action
from settings import brokers, icat_user, icat_passcode
from database import transactions
import json
import logging
import sys

class StateAction(object):
    """
        Base class for processing messages
    """
    def __init__(self, use_db_task=False):
        """
            Initialization
            @param use_db_task: if True, a task definition will be looked for in the DB when executing the action
        """
        self._user_db_task = use_db_task

    def _call_default_task(self, headers, message):
        """
            Find a default task for the given message header
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        # Convert the message queue name into a class name
        destination = headers["destination"].replace('/queue/','')
        destination = destination.replace('.', '_')
        destination = destination.capitalize()
        
        # Find a custom action for this message
        if destination in globals():
            action_cls = globals()[destination]
            action_cls()(headers, message)
            
    def _call_db_task(self, task_data, headers, message):
        """
            @param task_data: JSON-encoded task definition
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        task_def = json.loads(task_data)
        if 'task_class' in task_def and len(task_def['task_class'].strip())>0:
            try:
                toks = task_def['task_class'].strip().split('.')
                module = '.'.join(toks[:len(toks)-1])
                cls = toks[len(toks)-1]
                exec "from %s import %s as action_cls" % (module, cls)
                action_cls()(headers, message)
            except:
                logging.error("Task [%s] failed: %s" % (headers["destination"], sys.exc_value))
        if 'task_queues' in task_def:
            for item in task_def['task_queues']:
                self.send(destination='/queue/%s'%item, message=message, persistent='true')
        
                headers = {'destination': destination, 
                          'message-id': ''}
                transactions.add_status_entry(headers, message)
        
    @logged_action
    def __call__(self, headers, message):
        """
            Called to process a message
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        # Find task definition in DB if available
        if self._user_db_task:
            task_data = transactions.get_task(headers, message)
            if task_data is not None:
                self._call_db_task(task_data, headers, message)
                return
            
        # If we made it here we need to use default tasks
        self._call_default_task(headers, message)
    
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
        
        headers = {'destination': destination, 
                  'message-id': ''}
        transactions.add_status_entry(headers, message)
        
        # Sometimes the socket gets wiped out before we get a chance to complete
        # disconnecting
        try:
            conn.disconnect()
        except:
            logging.info("Send socket already closed: skipping disconnection")


class Postprocess_data_ready(StateAction):
    def __call__(self, headers, message):
        """
            Called to process a message
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        # Tell workers for start processing
        self.send(destination='/queue/CATALOG.DATA_READY', message=message, persistent='true')
        self.send(destination='/queue/REDUCTION.DATA_READY', message=message, persistent='true')
        
        
class Reduction_complete(StateAction):
    def __call__(self, headers, message):
        """
            Called to process a message
            @param headers: message headers
            @param message: JSON-encoded message content
        """
        # Tell workers to catalog the output
        self.send(destination='/queue/REDUCTION_CATALOG.DATA_READY', message=message, persistent='true')
