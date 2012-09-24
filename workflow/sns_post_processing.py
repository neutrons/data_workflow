from workflow_manager import WorkflowManager
from settings import brokers, icat_user, icat_passcode
from daemon import Daemon
import sys
import os

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

class WorkflowDaemon(Daemon):
    def run(self):
        mng = WorkflowManager(brokers, icat_user, icat_passcode, queues, False)
        mng.processing_loop()

if __name__ == "__main__":
    # Check whether the output directory exists
    out_dir = '/var/log/workflow'
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    
    daemon = WorkflowDaemon('/tmp/workflow.pid',
                            stdout=os.path.join(out_dir, 'output.log'),
                            stderr=os.path.join(out_dir, 'error.log'))
    
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)