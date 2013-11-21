import httplib
import json
import logging
import sys

STATUS_HOST = 'neutrons.ornl.gov'
def get_ops_status(instrument):
    """
        Pull the legacy status information
    """
    try:
        conn = httplib.HTTPConnection(STATUS_HOST, timeout=0.5)
        conn.request('GET', '/%s/status/data.json' % instrument.lower())
        r = conn.getresponse()
        data = json.loads(r.read())
        key_value_pairs = []

        for group in data.keys():
            for item in data[group].keys():
                key_value_pairs.append({'key':item.replace(' ', '_'),
                                        'value': data[group][item]})
        return key_value_pairs
    except:
        logging.error("Could not connect to status page: %s" % sys.exc_value)
        return []
