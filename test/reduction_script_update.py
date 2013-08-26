"""
    Send workflow notification message for a reduction script change
"""
import stomp
import json
import argparse
import time
from workflow.settings import brokers, icat_user, icat_passcode
   
def send_msg(instrument="HYSA"):
    """
        Send simple ActiveMQ message
        @param instrument: instrument name
    """
    data_dict = {"src_name": instrument,
                 "status": 0,
                 "information": "Reduction script changed"}
    data = json.dumps(data_dict)
    destination = "/topic/SNS.%s.STATUS.REDUCTION_SCRIPT" % instrument.upper()
    
    conn = stomp.Connection(host_and_ports=brokers, 
                            user=icat_user, passcode=icat_passcode, 
                            wait_on_receipt=True)
    conn.start()
    conn.connect()
    conn.send(destination=destination, message=data, persistent='true')
    conn.disconnect()
    time.sleep(0.1)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Reduction script change notification')
    parser.add_argument('-b', metavar='instrument', help='instrument name', required=True, dest='instrument')
    namespace = parser.parse_args()
    send_msg(instrument=namespace.instrument)
    

