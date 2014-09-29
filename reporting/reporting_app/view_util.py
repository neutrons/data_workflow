"""
    Utilities common to the whole web application.
    
    @copyright: 2014 Oak Ridge National Laboratory
"""
from django.conf import settings
import sys
import logging

def send_activemq_message(destination, data):
    """
        Send an AMQ message to the workflow manager.
        
        @param destination: queue to send the request to
        @param data: JSON data payload for the message
    """
    from workflow.settings import brokers, icat_user, icat_passcode
    import stomp
    if stomp.__version__[0]<4:
        # Shuffle the brokers so that we make sure we never get stuck
        # regardless of configuration and network problem.
        import random
        random.shuffle(brokers)
        conn = stomp.Connection(host_and_ports=brokers, 
                                user=icat_user, 
                                passcode=icat_passcode, 
                                wait_on_receipt=True,
                                timeout=10.0)
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=data, persistent='true')
    else:
        conn = stomp.Connection(host_and_ports=brokers)
        conn.start()
        conn.connect(icat_user, icat_passcode, wait=True)
        conn.send(destination, data, persistent='true')
    conn.disconnect()

def reduction_setup_url(instrument):
    """
        Check whether the reduction app is installed, and if so
        return a URL for the reduction setup if it's enabled 
        for the given instrument
        @param instrument: instrument name
    """
    try:
        if 'reduction' in settings.INSTALLED_APPS:
            import reduction.view_util
            return reduction.view_util.reduction_setup_url(instrument)
    except:
        logging.error("Error getting reduction setup url: %s" % sys.exc_value)
    return None