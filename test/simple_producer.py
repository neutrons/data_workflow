"""
    Example of a simple non-listening producer
"""
import stomp
import json
import time
import sys
import argparse
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
    
def send_msg(runid=1234, ipts=5678, 
             queue='POSTPROCESS.DATA_READY',
             info=None, error=None):
    """
        Send simple ActiveMQ message
        @param runid: run number (int)
        @param ipts: IPTS number (int)
        @param queue: ActiveMQ queue to send message to
        @param info: optional information message
        @param error: optional error message
    """
    data_dict = {"instrument": "HYSA",
             "ipts": "IPTS-%d" % ipts,
             "run_number": runid,
             "data_file": 'optional'}
    
    # Add info/error as needed
    if info is not None:
        data_dict["information"]=info
    if error is not None:
        data_dict["error"]=error

    data = json.dumps(data_dict)
    send(queue, data, persistent='true')
    time.sleep(0.1)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Workflow manager test producer')
    parser.add_argument('-r', metavar='runid', type=int, help='Run number (int)', dest='runid')
    parser.add_argument('-i', metavar='ipts', type=int, help='IPTS number (int)', dest='ipts')
    parser.add_argument('-q', metavar='queue', help='ActiveMQ queue name', dest='queue')
    namespace = parser.parse_args()
    
    ipts = 5678 if namespace.ipts is None else namespace.ipts
    runid = 1234 if namespace.runid is None else namespace.runid
    queue = 'POSTPROCESS.DATA_READY' if namespace.queue is None else namespace.queue
    
    print "Sending %s for IPTS-%g, run %g" % (queue, ipts, runid)
    send_msg(runid, ipts, queue=queue)
    

