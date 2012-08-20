"""
    Example of a simple non-listening producer
"""
import stomp
import json


# List of brokers
brokers = [("mac83808.ornl.gov", 61613), 
           ("mac83086.ornl.gov", 61613)]

icat_user = "icat"
icat_passcode = "icat"

def send(destination, message):
    """
        Send a message to a queue
        @param destination: name of the queue
        @param message: message content
    """
    conn = stomp.Connection(host_and_ports=brokers, 
                    user=icat_user, passcode=icat_passcode, 
                    wait_on_receipt=True, version=1.0)
    conn.start()
    conn.connect()
    conn.send(destination=destination, message=message)
    conn.disconnect()
    
    
data_dict = {"instrument": "HYSA",
             "ipts": "IPTS-%d" % 5678,
             "run_number": 1234,
             "data_file": 'optional'}

data = json.dumps(data_dict)

send('LIVEDATA.UPDATE', data)

