import httplib
import xml.dom.minidom
import sys
import os
import stomp
import json
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "database.settings")
# The report database module must be on the python path for Django to find it 
sys.path.append(os.path.abspath('database'))

# List of brokers
brokers = [("mac83808.ornl.gov", 61613), 
           ("mac83086.ornl.gov", 61613)]

icat_user = "icat"
icat_passcode = "icat"

def send(destination, message):
    """
        Send a message to a queue
        @param destination: name of the queue
        @param message: message content
    """
    conn = stomp.Connection(host_and_ports=brokers, 
                    user=icat_user, passcode=icat_passcode, 
                    wait_on_receipt=True, version=1.0)
    conn.start()
    conn.connect()
    conn.send(destination=destination, message=message)
    conn.disconnect()

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
                                      8080, timeout=5.0)
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
        print "Communication with ICAT server failed: %s" % sys.exc_value
        
    return run_info

def get_event_nexus_file(instrument, run_number):
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=15)
        url = '/icat-rest-ws/datafile/SNS/%s/%s' % (instrument.upper(), run_number)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        locations = dom.getElementsByTagName('location')
        for f in locations:
            file_path = get_text_from_xml(f.childNodes)
            file_name = os.path.basename(file_path)
            if file_name.startswith("%s_%s" % (instrument.upper(), run_number)) and \
                file_name.endswith("_event.nxs"):
                return file_path
    except:
        print "Communication with ICAT server failed (%s): %s" % (url, sys.exc_value)
        
    return 'unknown'

def get_ipts_list(instrument):
    ipts_list = []
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=2.5)
        url = '/icat-rest-ws/experiment/SNS/%s' % (instrument.upper())
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        locations = dom.getElementsByTagName('proposal')
        for f in locations:
            ipts_list.append(get_text_from_xml(f.childNodes))
    except:
        print "Communication with ICAT server failed (%s): %s" % (url, sys.exc_value)
        
    return ipts_list

def get_run_range(instrument, ipts):
    try:
        conn = httplib.HTTPConnection('icat.sns.gov', 
                                      8080, timeout=2.5)
        url = '/icat-rest-ws/experiment/SNS/%s/%s' % (instrument.upper(), ipts)
        conn.request('GET', url)
        r = conn.getresponse()
        dom = xml.dom.minidom.parseString(r.read())
        runs = dom.getElementsByTagName('runRange')
        if len(runs)>0:
            run_range_str = get_text_from_xml(runs[0].childNodes)
            run_range_str = run_range_str.replace(',','-')
            toks = run_range_str.split('-')
            return range(int(toks[0].strip()), int(toks[1].strip()))
    except:
        print "Communication with ICAT server failed (%s): %s" % (url, sys.exc_value)
    return []

if __name__ == '__main__':
    from database.report.models import DataRun
    instrument = 'EQSANS'
    ipts_list =  get_ipts_list(instrument)
    for ipts in ipts_list:
        runs = get_run_range(instrument, ipts)
        print ipts
        for run in runs:
            if DataRun.objects.filter(instrument_id__name=instrument.lower(),
                                      run_number=run).count()>0:
                continue
            file_path = get_event_nexus_file(instrument, run)
            data_dict = {"instrument": instrument,
                         "ipts": ipts,
                         "run_number": run,
                         "data_file": file_path}
            
            data = json.dumps(data_dict)
            
            send('POSTPROCESS.INFO', data)
    