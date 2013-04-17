import httplib
import xml.dom.minidom
import logging
import sys
import datetime
try:
    from workflow.database.settings import ICAT_DOMAIN, ICAT_PORT
except:
    ICAT_DOMAIN = 'icat.sns.gov'
    ICAT_PORT = 2080

def get_text_from_xml(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def get_ipts_info(instrument, ipts):
    run_info = {}
    
    # Get basic run info
    try:
        conn = httplib.HTTPConnection(ICAT_DOMAIN, 
                                      ICAT_PORT, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/meta' % (instrument.upper(),
                                                                      ipts.upper()))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        metadata = dom.getElementsByTagName('metadata')
        if len(metadata)>0:
            for n in metadata[0].childNodes:
                # Run title
                if n.nodeName=='title' and n.hasChildNodes():
                    run_info['title'] = get_text_from_xml(n.childNodes)
                # IPTS
                if n.nodeName=='proposal' and n.hasChildNodes():
                    run_info['proposal'] = get_text_from_xml(n.childNodes)
                # Time
                if n.nodeName=='createTime' and n.hasChildNodes():
                    timestr = get_text_from_xml(n.childNodes)
                    try:
                        tz_location = timestr.rfind('+')
                        if tz_location<0:
                            tz_location = timestr.rfind('-')
                        if tz_location>0:
                            date_time_str = timestr[:tz_location]
                            tz_str = timestr[tz_location:]
                            run_info['createTime'] = datetime.datetime.strptime(date_time_str, "%Y-%m-%dT%H:%M:%S.%f")
                    except:
                        logging.error("Communication with ICAT server failed (%s): %s" % (url, sys.exc_value))
                    
    except:
        logging.error("Communication with ICAT server failed: %s" % sys.exc_value)
    return run_info
    
def get_run_info(instrument, ipts, run_number):
    # Get basic experiment info
    run_info = get_ipts_info(instrument, ipts)
    
    # Get file location
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=1.0)
        url = '/icat-rest-ws/datafile/SNS/%s/%s' % (instrument.upper(), run_number)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        locations = dom.getElementsByTagName('location')
        data_paths = []
        reduced_paths = []
        for f in locations:
            filepath = get_text_from_xml(f.childNodes)
            if filepath.find("autoreduce")<0:
                data_paths.append(filepath)
            else:
                reduced_paths.append(filepath)
        
        run_info['data_files'] = data_paths
        run_info['reduced_files'] = reduced_paths
    except:
        logging.error("Communication with ICAT server failed (%s): %s" % (url, sys.exc_value))
        
    return run_info
