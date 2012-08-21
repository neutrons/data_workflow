import httplib
import xml.dom.minidom
import logging
import sys

def get_text_from_xml(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def get_run_info(instrument, ipts, run_number):
    run_info = {}
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=0.5)
        conn.request('GET', '/icat-rest-ws/experiment/SNS/%s/%s/%s' % (instrument.upper(),
                                                                      ipts,
                                                                      run_number))
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        metadata = dom.getElementsByTagName('metadata')
        if len(metadata)>0:
            for n in metadata[0].childNodes:
                # Run title
                if n.nodeName=='title' and n.hasChildNodes():
                    run_info['title'] = get_text_from_xml(n.childNodes)
    except:
        logging.error("Communication with ICAT server failed: %s" % sys.exc_value)
        
    return run_info

def get_event_nexus_file(instrument, run_number):
    run_info = {}
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=0.5)
        url = '/icat-rest-ws/datafile/SNS/%s/%s' % (instrument.upper(), run_number)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        locations = dom.getElementsByTagName('location')
        for f in locations:
            print f
            print get_text_from_xml(f.childNodes)
    except:
        logging.error("Communication with ICAT server failed (%s): %s" % (url, sys.exc_value))
        
    return run_info

