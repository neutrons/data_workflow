#!/usr/bin/env python3
"""
PROTOTYPE: Post-processing tasks with per-instrument queue support

Key changes:
1. Use configuration.matches_processor_queue() for flexible queue matching
2. Supports both exact matches (legacy) and per-instrument patterns

Example flow:
  Message arrives from: REDUCTION.EQSANS.DATA_READY
  Matches processor: ReductionProcessor (base queue: REDUCTION.DATA_READY)
  Routes correctly via pattern matching

@copyright: 2014 Oak Ridge National Laboratory
"""

import importlib
import json
import logging
import os
import socket
import sys

import stomp


class PostProcessAdmin:
    def __init__(self, data, conf):
        logging.debug("json data: %s [%s]", str(data), type(data))
        if not isinstance(data, dict):
            raise ValueError("PostProcessAdmin expects a data dictionary")
        data["information"] = socket.gethostname()
        self.data = data
        self.conf = conf

        # List of error messages to be handled as information
        self.exceptions = self.conf.exceptions

        self.data_file = None
        self.facility = None
        self.instrument = None
        self.proposal = None
        self.run_number = None

    def send(self, destination, data):
        """
        Send an AMQ message
        @param destination: AMQ queue to send to
        @param data: payload of the message
        """
        logging.info("%s: %s", destination, data)
        conn = stomp.Connection(host_and_ports=self.conf.brokers)
        conn.connect(self.conf.amq_user, self.conf.amq_pwd, wait=True)
        conn.send(destination, data.encode())
        conn.disconnect()


if __name__ == "__main__":
    import argparse

    from postprocessing.Configuration import read_configuration

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s/%(process)d %(message)s")

    parser = argparse.ArgumentParser(description="Post-processing agent")
    parser.add_argument("-q", metavar="queue", help="ActiveMQ queue name", dest="queue", required=True)
    parser.add_argument("-c", metavar="config", help="Configuration file", dest="config")
    parser.add_argument("-d", metavar="data", help="JSON data", dest="data")
    parser.add_argument("-f", metavar="data_file", help="Nexus data file", dest="data_file")
    namespace = parser.parse_args()

    try:
        # Refresh configuration is we need to use an alternate configuration
        if namespace.config is not None:
            configuration = read_configuration(namespace.config)
        else:
            configuration = read_configuration()

        # If we have no data dictionary, try to create one
        if namespace.data is None:
            if namespace.data_file is not None:
                data = {"facility": "SNS", "data_file": namespace.data_file}
                file_name = os.path.basename(namespace.data_file)
                toks = file_name.split("_")
                if len(toks) > 1:
                    data["instrument"] = toks[0].upper()
                    try:
                        data["run_number"] = str(int(toks[1]))
                    except:  # noqa: E722
                        logging.error("Could not determine run number")
                    ipts_toks = namespace.data_file.upper().split(toks[0].upper())
                    if len(ipts_toks) > 1:
                        sep_toks = ipts_toks[1].split("/")
                        if len(sep_toks) > 1:
                            data["ipts"] = sep_toks[1]
            else:
                logging.error("PostProcessAdmin: Expected a JSON object or a file path")
        else:
            data = json.loads(namespace.data)

        # Process the data
        try:
            pp = PostProcessAdmin(data, configuration)

            # Check for registered processors
            processor_matched = False
            if isinstance(configuration.processors, list):
                for p in configuration.processors:
                    toks = p.split(".")
                    if len(toks) == 2:
                        processor_module = importlib.import_module(f"postprocessing.processors.{toks[0]}")
                        try:
                            processor_class = getattr(processor_module, toks[1])
                            base_queue = processor_class.get_input_queue_name()

                            # NEW: Use flexible pattern matching instead of exact equality
                            # This supports both:
                            #   - Exact match: REDUCTION.DATA_READY == REDUCTION.DATA_READY
                            #   - Pattern match: REDUCTION.EQSANS.DATA_READY matches REDUCTION.DATA_READY
                            if configuration.matches_processor_queue(namespace.queue, base_queue):
                                logging.info(
                                    "Matched queue %s to processor %s (base queue: %s)",
                                    namespace.queue,
                                    toks[1],
                                    base_queue,
                                )
                                # Instantiate and call the processor
                                proc = processor_class(data, configuration, send_function=pp.send)
                                proc()
                                processor_matched = True
                                break  # Stop after first match

                        except:  # noqa: E722
                            logging.error(
                                "PostProcessAdmin: Processor error: %s",
                                sys.exc_info()[1],
                            )
                            raise
                    else:
                        logging.error(
                            "PostProcessAdmin: Processors can only be specified in the format module.Processor_class"
                        )

            if not processor_matched:
                logging.warning(
                    "PostProcessAdmin: No processor matched queue %s",
                    namespace.queue,
                )

        except:  # noqa: E722
            # If we have a proper data dictionary, send it back with an error message
            if isinstance(data, dict):
                data["error"] = str(sys.exc_info()[1])
                conn = stomp.Connection(host_and_ports=configuration.brokers)
                conn.connect(configuration.amq_user, configuration.amq_pwd, wait=True)
                conn.send(configuration.postprocess_error, json.dumps(data).encode())
                conn.disconnect()
            raise
    except:  # noqa: E722
        logging.error("PostProcessAdmin: %s", sys.exc_info()[1])
