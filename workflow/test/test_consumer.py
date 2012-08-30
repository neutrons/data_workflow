"""
    Dummy client to simulate the worker nodes
"""
import time
import stomp
from workflow.settings import *

class Listener(stomp.ConnectionListener):
    def __init__(self, ):
        self.connected = False

    def on_receipt(self, headers, body):
        print "RECEIPT: %s" % headers
        
    def send(self, destination, message):
        conn = stomp.Connection(host_and_ports=brokers, 
                        user="icat", passcode="icat", 
                        wait_on_receipt=True)
        conn.set_listener('worker_bee', self)
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=message)
        conn.disconnect()
        print "  -> %s" % destination
        
    def on_message(self, headers, message):
        print "<--- %s: %s" % (headers["destination"], message)
        destination = headers["destination"] 
        if destination=='/queue/REDUCTION.DATA_READY':
            self.send('/queue/REDUCTION.STARTED', message)
            self.send('/queue/REDUCTION.COMPLETE', message)
        elif destination=='/queue/CATALOG.DATA_READY':
            self.send('/queue/CATALOG.STARTED', message)
            self.send('/queue/CATALOG.COMPLETE', message)
        elif destination=='/queue/REDUCTION_CATALOG.DATA_READY':
            self.send('/queue/REDUCTION_CATALOG.STARTED', message)
            self.send('/queue/REDUCTION_CATALOG.COMPLETE', message)
        
    def on_disconnected(self):
        self.connected = False
        
    def subscribe(self):
        conn = stomp.Connection(host_and_ports=brokers, 
                                user="icat", passcode="icat", 
                                wait_on_receipt=True)
        conn.set_listener('worker_bee', self)
        conn.start()
        conn.connect(wait=True)
        conn.subscribe(destination='/queue/CATALOG.DATA_READY', ack='auto')
        conn.subscribe(destination='/queue/REDUCTION.DATA_READY', ack='auto')
        conn.subscribe(destination='/queue/REDUCTION_CATALOG.DATA_READY', ack='auto')
        print "Connected to %s:%d\n" % conn.get_host_and_port()
        self.connected = True
        return conn
        
    def listen(self):
        _listen = True
        conn = None
        while(_listen):
            try:
                conn = self.subscribe()
                while(self.connected):
                    time.sleep(1)
            except KeyboardInterrupt:
                print "\nStopping"
                _listen = False
            except:
                print "\nReconnecting..."
                time.sleep(3.0)
            finally:
                _listen = False
                if conn is not None and conn.is_connected():
                    conn.disconnect()

Listener().listen()

