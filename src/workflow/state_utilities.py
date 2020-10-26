import logging
from database import transactions
import json
import sys

def decode_message(message):
    """
        Decode message and turn it into a dictionnary 
        we can understand.
        
        Messages from streaming translation are expected to be an absolute path
        of the following type:
        
        Old system: /SNS/EQSANS/IPTS-1234/.../EQSANS_5678_event.nxs
        ADARA:      /SNS/EQSANS/IPTS-1234/nexus/EQSANS_5678.nxs.h5
        
        Calibration runs, etc... have 2009_06_24_CAL instead
        of IPTS-xxxx
    """
    tokens = message.split('/')
    if len(tokens)<6:
        raise RuntimeError, "Badly formed message from streaming translation\n  %s" % message
    
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
    
    # Create payload for the message
    data = {"instrument": tokens[2].lower(),
            "facility": tokens[1].upper(),
            "ipts": tokens[3].lower(),
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
        logging.info("%s r%s: %s: %s" % (data["instrument"],
                                         data["run_number"],
                                         destination,
                                         str(data)))
        transactions.add_status_entry(headers, message)
        
        # Clean up the extra information 
        if data.has_key('information'):
            del data['information']
        if data.has_key('error'):
            del data['error']
        message = json.dumps(data)
        
        return action(self, headers, message)

    return process_function