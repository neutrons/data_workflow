"""
    Utilities common to the whole web application.
    
    @copyright: 2014 Oak Ridge National Laboratory
"""
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
