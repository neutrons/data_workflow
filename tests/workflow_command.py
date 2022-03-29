"""
    ActiveMQ client used to issue commands to the post-processing workflow.
    NOTE: Only works for runs that are already in the DB
"""
from report.models import Instrument, DataRun
from workflow.settings import brokers, icat_user, icat_passcode
import argparse
import sys
import os
import json
import time
import stomp
import logging

logging.getLogger().setLevel(logging.INFO)

if os.path.isfile("settings.py"):
    logging.warning("Using local settings.py file")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dasmon_listener.settings")

INSTALLATION_DIR = "/var/www/workflow/app"
sys.path.append(INSTALLATION_DIR)


def send(destination, message, persistent="true"):
    """
    Send a message to a queue

    :param destination: name of the queue
    :param message: message content
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


def fetch_data(instrument, run):
    """
    Put together a dictionary that the post-processing will
    be able to process.

    :param instrument: instrument short name
    :param run: run number
    """
    # Find the instrument
    try:
        instrument_id = Instrument.objects.get(name=instrument.lower())
    except:  # noqa: E722
        logging.error("Could not find instrument %s" % instrument)
        return

    # Check whether the run exists
    try:
        run_id = DataRun.objects.get(instrument_id=instrument_id, run_number=int(run))
        logging.info("Found run %s" % run_id)
    except:  # noqa: E722
        logging.info("Could not find run %s for %s" % (run, instrument))
        logging.error(sys.exc_value)
        return

    # Build up dictionary
    data_dict = {
        "facility": "SNS",
        "instrument": instrument,
        "ipts": run_id.ipts_id.expt_name.upper(),
        "run_number": run,
        "data_file": run_id.file,
    }
    print(data_dict)


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
        "-b",
        metavar="instrument",
        help="instrument name",
        required=True,
        dest="instrument",
    )
    parser.add_argument(
        "--post_process",
        help="Perform full post-processing",
        action="store_true",
        dest="do_post_process",
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

    queue = None
    if namespace.do_post_process is not None and namespace.do_post_process is True:
        queue = "POSTPROCESS.DATA_READY"
    if namespace.do_catalog is not None and namespace.do_catalog is True:
        queue = "CATALOG.DATA_READY"
    if namespace.do_reduction is not None and namespace.do_reduction is True:
        queue = "REDUCTION.DATA_READY"
    if namespace.do_reduction_catalog is not None and namespace.do_reduction_catalog is True:
        queue = "REDUCTION_CATALOG.DATA_READY"

    data_dict = fetch_data(namespace.instrument, namespace.runid)
    if queue is not None:
        logging.info("Sending message to %s" % queue)
        data = json.dumps(data_dict)
        send(queue, data, persistent="true")
        time.sleep(0.1)
