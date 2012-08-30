from workflow_manager import WorkflowManager
from settings import *

# List of queues to listen to. Each queue must have a
# corresponding class in states.py
queues = ['POSTPROCESS.DATA_READY',
          'CATALOG.STARTED',
          'CATALOG.COMPLETE',
          'REDUCTION.STARTED',
          'REDUCTION.DISABLED',
          'REDUCTION.COMPLETE',
          'REDUCTION.NOT_NEEDED',
          'REDUCTION_CATALOG.STARTED',
          'REDUCTION_CATALOG.COMPLETE',
          'POSTPROCESS.INFO',
          'POSTPROCESS.ERROR']

mng = WorkflowManager(brokers, icat_user, icat_passcode, queues)
mng.processing_loop()
