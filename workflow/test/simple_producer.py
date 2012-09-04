"""
    Example of a simple non-listening producer
"""
import stomp
import json
from workflow.settings import *


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
    
    
data_dict = {"instrument": "HYSA",
             "ipts": "IPTS-%d" % 5678,
             "run_number": 1242,
             "data_file": 'optional'}

data = json.dumps(data_dict)

send('LIVEDATA.UPDATE', data, persistent='true')
#send('CATALOG.DATA_READY', data)
send('POSTPROCESS.DATA_READY', data, persistent='true')

