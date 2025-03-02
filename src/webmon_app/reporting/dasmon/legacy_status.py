"""
Get the status of legacy instruments

@author: M. Doucet, Oak Ridge National Laboratory
@copyright: 2015 Oak Ridge National Laboratory
"""

import httplib2
import json
import logging
from reporting.dasmon.models import LegacyURL

STATUS_HOST = "neutrons.ornl.gov"


def get_ops_status(instrument_id):
    """
    Pull the legacy status information

    :param instrument_id: Instrument object
    """
    try:
        url = get_legacy_url(instrument_id, False)
        if url.startswith("http"):
            toks = url.split("/")
            status_host = toks[2]
        else:
            status_host = STATUS_HOST
        conn = httplib2.HTTPSConnectionWithTimeout(status_host, timeout=0.5)
        conn.request("GET", url)
        r = conn.getresponse()
        data = json.loads(r.read())
        organized_data = []
        groups = sorted(data.keys())
        for group in groups:
            key_value_pairs = []
            keys = sorted(data[group].keys())
            for item in keys:
                key_value_pairs.append(
                    {
                        "key": item.replace(" ", "_")
                        .replace("(%)", "[pct]")
                        .replace("(", "[")
                        .replace(")", "]")
                        .replace("#", ""),
                        "value": data[group][item],
                    }
                )
            organized_data.append({"group": group, "data": key_value_pairs})
        return organized_data
    except:  # noqa: E722
        logging.warning("Could not get legacy DAS status:", exc_info=True)
        return []


def get_legacy_url(instrument_id, include_domain=True):
    """
    Generate URL for legacy instrument status data

    :param instrument_id: Instrument object
    :param include_domain: True if we need to return a complete URL
    """
    try:
        url_obj = LegacyURL.objects.get(instrument_id=instrument_id)
        url = url_obj.url
    except:  # noqa: E722
        url = "/sites/default/files/instruments/%s-data.json" % instrument_id.name

    if include_domain and not url.startswith("http"):
        url = "http://%s%s" % (STATUS_HOST, url)
    return url
