import logging
from database import transactions
import json
import sys

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