"""
    Perform DB transactions
"""
import os
import sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "database.settings")

# The report database module must be on the python path for Django to find it 
sys.path.append(os.path.dirname(__file__))

# Import your models for use in your script
from database.report.models import DataRun, RunStatus, StatusInfo

def add_status_entry(headers, message):
    """
        Populate the reporting database with the contents
        of a status message of the following format:
        
        headers: {'expires': '0', 'timestamp': '1344613053723', '
                  destination': '/queue/POSTPROCESS.DATA_READY', 
                  'persistent': 'true', 'priority': '5', 
                  'message-id': 'ID:mac83086.ornl.gov-59780-1344536680877-8:2:1:1:1'}
    """
    destination = headers["destination"].replace('/queue/','')
    status_id = StatusInfo.objects.filter(name__startswith=destination)
    if len(status_id)==0:
        status_id = StatusInfo(name=destination)
        status_id.save()
    else:
        status_id = status_id[0]
    
    # Check whether we already have an entry for this run
    #TODO: replace message content by proper data
    run_number = int(message)
    run_ids = DataRun.objects.filter(run_number=run_number)
    
    if len(run_ids)>0:
        run_id = run_ids[0]
    else:
        run_id = DataRun(run_number=run_number)
        run_id.save()
    
    run_status = RunStatus(run_id=run_id,
                           queue_id=status_id,
                           message_id=headers["message-id"])
    run_status.save()
    