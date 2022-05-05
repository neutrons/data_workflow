#!/usr/bin/env python
import os
import time
import stomp


class Listener(stomp.ConnectionListener):
    def on_message(self, frame) -> None:
        if frame.headers["destination"] == "/queue/CATALOG.DATA_READY":
            conn.send("/queue/CATALOG.STARTED", frame.body)
            time.sleep(0.1)
            conn.send("/queue/CATALOG.COMPLETE", frame.body)
        else:
            conn.send("/queue/REDUCTION_CATALOG.STARTED", frame.body)
            time.sleep(0.1)
            conn.send("/queue/REDUCTION_CATALOG.COMPLETE", frame.body)


if __name__ == "__main__":
    # Parse ENV vars
    ICAT_USER = os.environ.get("ICAT_USER", default="icat")
    ICAT_PASSCODE = os.environ.get("ICAT_PASSCODE", default="icat")
    PORTS = os.environ.get("ACTIVE_MQ_PORTS", default=61613)
    BROKERS = [(os.environ.get("ACTIVE_MQ_HOST", default="activemq"), int(PORTS))]

    # Start the connection
    conn = stomp.Connection(host_and_ports=BROKERS)
    conn.set_listener("", Listener())
    conn.connect(ICAT_USER, ICAT_PASSCODE, wait=True)
    conn.subscribe(destination="/queue/CATALOG.DATA_READY", id=1, ack="auto")
    conn.subscribe(destination="/queue/REDUCTION_CATALOG.DATA_READY", id=1, ack="auto")

    while conn.is_connected():
        time.sleep(1)
