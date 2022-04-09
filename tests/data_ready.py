#!/usr/bin/env python
import stomp
import json

brokers = [("localhost", 61613)]
icat_user = "icat"
icat_passcode = "icat"


def send_msg(destination, message):
    conn = stomp.Connection(host_and_ports=brokers)
    conn.connect(icat_user, icat_passcode, wait=True)
    conn.send(destination, json.dumps(message))
    conn.disconnect()


def create_run(instrument, ipts, run_number, facility="SNS"):
    send_msg(
        "/queue/POSTPROCESS.DATA_READY",
        {
            "instrument": instrument,
            "facility": facility,
            "ipts": f"IPTS-{ipts}",
            "run_number": run_number,
            "data_file": f"/{facility}/{instrument}/IPTS-{ipts}/nexus/{instrument}_{run_number}.nxs.h5",
        },
    )


create_run("HYSA", 1234, 12345)

create_run("ARCS", 27278, 214581)
create_run("ARCS", 27800, 201562)
create_run("ARCS", 27800, 214583)
