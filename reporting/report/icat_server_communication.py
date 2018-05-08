#pylint: disable=bare-except, invalid-name, too-many-locals, too-many-branches, too-many-nested-blocks
"""
    Utilities to communicate with ICAT server

    @author: M. Doucet, Oak Ridge National Laboratory
    @copyright: 2015 Oak Ridge National Laboratory
"""
import sys
import httplib
import xml.dom.minidom
import logging
import datetime
try:
    from django.conf import settings
    ICAT_DOMAIN = settings.ICAT_DOMAIN
    ICAT_PORT = settings.ICAT_PORT
except:
    logging.warning("Could not find ICAT config: %s", sys.exc_value)
    ICAT_DOMAIN = 'icat.sns.gov'
    ICAT_PORT = 2080

def get_text_from_xml(nodelist):
    """
        Get text from an XML node list
        @param nodelist: nodes
    """
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def decode_time(timestamp):
    """
        Decode timestamp and return a datetime object
    """
    try:
        tz_location = timestamp.rfind('+')
        if tz_location < 0:
            tz_location = timestamp.rfind('-')
        if tz_location > 0:
            date_time_str = timestamp[:tz_location]
            try:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                return datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S")
    except:
        logging.error("Could not parse timestamp '%s': %s", timestamp, sys.exc_value)
        return None

def get_run_info(instrument, ipts, run_number):
    """
        Get ICAT info for the specified run
    """
    run_info = {}
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN,
                                      ICAT_PORT, timeout=2.0)
        url = '/icat-rest-ws/dataset/SNS/%s/%s/lite' % (instrument.upper(), run_number)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        locations = dom.getElementsByTagName('location')
        data_paths = []
        reduced_paths = []
        for f in locations:
            filepath = get_text_from_xml(f.childNodes)
            if filepath.find("autoreduce") < 0:
                data_paths.append(filepath)
            else:
                reduced_paths.append(filepath)

        run_info['data_files'] = data_paths
        run_info['reduced_files'] = reduced_paths
        run_info['proposal'] = None

        metadata = dom.getElementsByTagName('metadata')
        if len(metadata) > 0:
            for n in metadata[0].childNodes:
                # Run title
                if n.nodeName == 'title' and n.hasChildNodes():
                    run_info['title'] = get_text_from_xml(n.childNodes)
                if n.nodeName == 'proposal' and n.hasChildNodes():
                    run_info['proposal'] = get_text_from_xml(n.childNodes)
                # Duration
                if n.nodeName == 'duration' and n.hasChildNodes():
                    value = get_text_from_xml(n.childNodes)
                    try:
                        run_info['duration'] = "%g sec" % float(value)
                    except:
                        run_info['duration'] = value
                # Basic info
                for item in ['totalCounts', 'protonCharge']:
                    if n.nodeName == item and n.hasChildNodes():
                        value = get_text_from_xml(n.childNodes)
                        try:
                            run_info[item] = "%g" % float(value)
                        except:
                            run_info[item] = value
                # Start time
                if n.nodeName == 'startTime' and n.hasChildNodes():
                    timestr = get_text_from_xml(n.childNodes)
                    run_info['startTime'] = decode_time(timestr)
                # End time
                if n.nodeName == 'endTime' and n.hasChildNodes():
                    timestr = get_text_from_xml(n.childNodes)
                    run_info['endTime'] = decode_time(timestr)
    except:
        logging.error("Communication with ICAT server failed (%s): %s", url, sys.exc_value)

    return run_info
