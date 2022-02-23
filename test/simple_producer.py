"""
    Example of a simple non-listening producer
"""
import stomp
import json
import time
import argparse
from workflow.settings import brokers, icat_user, icat_passcode


def send(destination, message, persistent="true"):
    """
    Send a message to a queue
    @param destination: name of the queue
    @param message: message content
    """
    if stomp.__version__[0] < 4:
        conn = stomp.Connection(
            host_and_ports=brokers,
            user=icat_user,
            passcode=icat_passcode,
            wait_on_receipt=True,
        )
        conn.start()
        conn.connect()
        conn.send(destination=destination, message=message, persistent=persistent)
    else:
        conn = stomp.Connection(host_and_ports=brokers)
        conn.start()
        conn.connect(icat_user, icat_passcode, wait=True)
        conn.send(destination, message)
    conn.disconnect()


def send_msg(
    runid=1234,
    ipts=5678,
    queue="POSTPROCESS.DATA_READY",
    info=None,
    error=None,
    data_file="",
    instrument="HYSA",
):
    """
    Send simple ActiveMQ message
    @param runid: run number (int)
    @param ipts: IPTS number (int)
    @param queue: ActiveMQ queue to send message to
    @param info: optional information message
    @param error: optional error message
    @param data_file: data file path to be sent in message
    @param instrument: instrument name
    """
    data_dict = {
        "instrument": instrument,
        "facility": "SNS",
        "ipts": "IPTS-%d" % ipts,
        "run_number": runid,
        "data_file": data_file,
    }

    # Add info/error as needed
    if info is not None:
        data_dict["information"] = info
    if error is not None:
        data_dict["error"] = error

    print("Sending %s: %s" % (queue, str(data_dict)))
    data = json.dumps(data_dict)
    send(queue, data, persistent="true")
    time.sleep(0.1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Workflow manager test producer")
    parser.add_argument(
        "-r",
        metavar="runid",
        type=int,
        help="Run number (int)",
        dest="runid",
        required=True,
    )
    parser.add_argument(
        "-i",
        metavar="ipts",
        type=int,
        help="IPTS number (int)",
        dest="ipts",
        required=True,
    )
    parser.add_argument("-q", metavar="queue", help="ActiveMQ queue name", dest="queue")
    parser.add_argument("-e", metavar="err", help="Error message", dest="err")
    parser.add_argument("-d", metavar="file", help="data file path", dest="file", required=True)
    parser.add_argument(
        "-b",
        metavar="instrument",
        help="instrument name",
        required=True,
        dest="instrument",
    )
    parser.add_argument("--catalog", help="Catalog the data", action="store_true", dest="do_catalog")
    parser.add_argument(
        "--reduction",
        help="Perform reduction",
        action="store_true",
        dest="do_reduction",
    )
    parser.add_argument(
        "--reduction_catalog",
        help="Perform cataloging of reduced data",
        action="store_true",
        dest="do_reduction_catalog",
    )

    namespace = parser.parse_args()

    default_queue = "POSTPROCESS.DATA_READY"
    if namespace.do_catalog is not None and namespace.do_catalog is True:
        default_queue = "CATALOG.DATA_READY"
    if namespace.do_reduction is not None and namespace.do_reduction is True:
        default_queue = "REDUCTION.DATA_READY"
    if namespace.do_reduction_catalog is not None and namespace.do_reduction_catalog is True:
        default_queue = "REDUCTION_CATALOG.DATA_READY"

    queue = default_queue if namespace.queue is None else namespace.queue
    file = "" if namespace.file is None else namespace.file
    err = namespace.err

    send_msg(
        namespace.runid,
        namespace.ipts,
        queue=queue,
        error=err,
        data_file=file,
        instrument=namespace.instrument,
    )
