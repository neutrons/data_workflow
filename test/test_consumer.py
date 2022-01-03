"""
    Dummy client to simulate the worker nodes
"""
from workflow.settings import brokers, icat_user, icat_passcode
from consumer import Consumer

queues = ['CATALOG.DATA_READY',
          'REDUCTION.DATA_READY',
          'REDUCTION_CATALOG.DATA_READY',
          'LIVEDATA.UPDATE']
print brokers
c = Consumer(brokers, icat_user, icat_passcode, queues)
c.processing_loop()
