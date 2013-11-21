import httplib
import json
import logging
import sys
from dasmon.models import LegacyURL

STATUS_HOST = 'neutrons.ornl.gov'
def get_ops_status(instrument_id):
    """
        Pull the legacy status information
    """
    try:
        conn = httplib.HTTPConnection(STATUS_HOST, timeout=0.5)
        url = get_legacy_url(instrument_id, False)
        conn.request('GET', '%s/data.json' % url)
        r = conn.getresponse()
        data = json.loads(r.read())
        key_value_pairs = []

        for group in data.keys():
            for item in data[group].keys():
                key_value_pairs.append({'key':item.replace(' ', '_').replace('(', '[').replace(')', ']'),
                                        'value': data[group][item]})
        return key_value_pairs
    except:
        logging.error("Could not connect to status page: %s" % sys.exc_value)
        return []

def get_legacy_url(instrument_id, include_domain=True):
    try:
        url_obj = LegacyURL.objects.get(instrument_id=instrument_id)
        url = url_obj.url
    except:
        url = '/%s/status/' % instrument_id.name
        
    if include_domain:
        url = 'http://%s%s' % (STATUS_HOST, url)
    return url
    