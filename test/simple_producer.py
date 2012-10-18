"""
    Example of a simple non-listening producer
"""
import stomp
import json
import time
from workflow.settings import brokers, icat_user, icat_passcode

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
    
for i in range(1234,1235):    
    data_dict = {"instrument": "HYSA",
             "ipts": "IPTS-%d" % 5678,
             "run_number": i,
             "data_file": 'optional',
             "information": 'some info',
             "error": 'some error'}

    data = json.dumps(data_dict)
    #send('LIVEDATA.UPDATE', data, persistent='true')
    #send('CATALOG.DATA_READY', data)
    #send('POSTPROCESS.INFO', data, persistent='true')
    send('POSTPROCESS.DATA_READY', data, persistent='true')
    time.sleep(0.1)
