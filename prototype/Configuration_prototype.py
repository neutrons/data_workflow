# pylint: disable=line-too-long, too-many-statements, too-few-public-methods, too-many-instance-attributes, invalid-name
"""
PROTOTYPE: Per-instrument queue support for Configuration.py

Key changes:
1. Add per_instrument_queues config parameter (default: False for backwards compatibility)
2. When enabled, transform queue names to wildcard patterns for subscription
3. Store both original patterns (for routing) and subscription patterns

Example:
  Original: REDUCTION.DATA_READY
  Subscription pattern: REDUCTION.*.DATA_READY (matches REDUCTION.EQSANS.DATA_READY, etc.)
"""

import importlib
import json
import logging
import os
import sys


class Configuration:
    """
    Read and process configuration file and provide an easy way to create a configured Client object
    """

    def __init__(self, config_file):
        try:
            with open(config_file, "r") as cfg:
                json_encoded = cfg.read()
        except (PermissionError, FileNotFoundError, OSError) as e:
            raise RuntimeError(f"Configuration file doesn't exist or is not readable: {config_file}") from e
        config = json.loads(json_encoded)

        # Keep a record of which config file we are using
        self.config_file = config_file
        # ActiveMQ user creds
        self.amq_user = config["amq_user"]
        self.amq_pwd = config["amq_pwd"]
        # ActiveMQ broker information
        self.failover_uri = config["failover_uri"]
        self.brokers = [(host, port) for host, port in config["brokers"]]
        self.sw_dir = config["sw_dir"] if "sw_dir" in config else "/opt/postprocessing"
        self.postprocess_error = config["postprocess_error"]

        # PER-INSTRUMENT QUEUE SUPPORT
        # When enabled, subscribes to wildcard patterns to receive messages from per-instrument queues
        self.per_instrument_queues = config.get("per_instrument_queues", False)

        # Reduction AMQ queues
        self.reduction_data_ready = (
            config["reduction_data_ready"] if "reduction_data_ready" in config else "REDUCTION.DATA_READY"
        )
        self.reduction_started = config["reduction_started"]
        self.reduction_complete = config["reduction_complete"]
        self.reduction_error = config["reduction_error"]
        self.reduction_disabled = config["reduction_disabled"]
        self.heartbeat_ping = (
            config["heartbeat_ping"] if "heartbeat_ping" in config else "/topic/SNS.COMMON.STATUS.PING"
        )
        # Reduction script writer
        self.create_reduction_script = (
            config["create_reduction_script"] if "create_reduction_script" in config else "REDUCTION.CREATE_SCRIPT"
        )
        self.service_status = (
            config["service_status"] if "service_status" in config else "/topic/SNS.${instrument}.STATUS.POSTPROCESS"
        )

        self.heart_beat = config["heart_beat"]
        self.log_file = config["log_file"] if "log_file" in config else "post_processing.log"
        # log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
        self.log_level = getattr(logging, config.get("log_level", ""), logging.INFO)
        self.start_script = config["start_script"] if "start_script" in config else "python"
        self.task_script = config["task_script"] if "task_script" in config else "PostProcessAdmin.py"
        self.python_dir = (
            config["python_dir"] if "python_dir" in config else os.path.join(self.sw_dir, "postprocessing")
        )
        self.mantid_path = config["mantid_path"] if "mantid_path" in config else "/opt/Mantid/bin"
        # used to override /facility/instrument/shared
        self.dev_instrument_shared = (
            config["dev_instrument_shared"].strip() if "dev_instrument_shared" in config else ""
        )
        # used to override /facility/instrument/proposal/shared
        self.dev_output_dir = config["dev_output_dir"].strip() if "dev_output_dir" in config else ""
        self.python_executable = config["python_exec"] if "python_exec" in config else "python3"

        self.max_procs = config["max_procs"] if "max_procs" in config else 5

        self.comm_only = config["communication_only"] == 1 if "communication_only" in config else False

        self.task_script_queue_arg = config["task_script_queue_arg"] if "task_script_queue_arg" in config else None
        self.task_script_data_arg = config["task_script_data_arg"] if "task_script_data_arg" in config else None

        self.exceptions = config["exceptions"] if "exceptions" in config else ["Error in logging framework"]

        self.jobs_per_instrument = config["jobs_per_instrument"] if "jobs_per_instrument" in config else 2

        self.calvera_ingest_url = config.get("calvera_ingest_url", "")
        self.intersect_ingest_url = config.get("intersect_ingest_url", "")

        self.oncat_url = config.get("oncat_url", "")
        self.oncat_api_token = config.get("oncat_api_token", "")

        # Image filepath metadata paths for cataloging image files
        # Default is for VENUS instrument, but can be configured per instrument
        default_image_metadata_paths = ["metadata.entry.daslogs.bl10:exp:im:imagefilepath.value"]
        self.image_filepath_metadata_paths = config.get("image_filepath_metadata_paths", default_image_metadata_paths)

        sys.path.insert(0, self.sw_dir)
        # Configure processor plugins
        default_processors = [
            "oncat_processor.ONCatProcessor",
            "oncat_reduced_processor.ONCatProcessor",
            "create_reduction_script_processor.CreateReductionScriptProcessor",
            "reduction_processor.ReductionProcessor",
        ]
        self.processors = config.get("processors", default_processors)

        # Store both original queue patterns (for routing) and subscription patterns
        self.queue_patterns = {}  # Maps subscription pattern -> original processor queue name
        self.queues = []  # List of queue patterns to subscribe to

        if isinstance(self.processors, list):
            for p in self.processors:
                toks = p.split(".")
                if len(toks) == 2:
                    # for instance, emulate `from oncat_processor import ONCatProcessor`
                    processor_module = importlib.import_module(  # noqa: F841
                        f"postprocessing.processors.{toks[0]}"
                    )
                    try:
                        processor_class = getattr(processor_module, toks[1])
                        base_queue = processor_class.get_input_queue_name()

                        # Transform to per-instrument pattern if enabled
                        subscription_queue = self._make_subscription_pattern(base_queue)

                        self.queues.append(subscription_queue)
                        self.queue_patterns[subscription_queue] = base_queue

                    except:  # noqa: E722
                        logging.error(
                            "Configuration: Error loading processor: %s",
                            sys.exc_info()[1],
                        )
                else:
                    logging.error(
                        "Configuration: Processors can only be specified in the format module.Processor_class"
                    )

        # Job memory monitoring
        self.system_mem_limit_perc = config.get("system_mem_limit_perc", 70.0)
        self.mem_check_interval_sec = config.get("mem_check_interval_sec", 0.2)

        # Job runtime monitoring
        self.task_time_limit_minutes = config.get("task_time_limit_minutes", 60.0)

    def _make_subscription_pattern(self, base_queue):
        """
        Transform a base queue name to a subscription pattern.

        If per_instrument_queues is enabled:
          REDUCTION.DATA_READY -> REDUCTION.*.DATA_READY
          CATALOG.ONCAT.DATA_READY -> CATALOG.*.DATA_READY

        Otherwise returns the original queue name (backwards compatible).

        Args:
            base_queue: Original queue name from processor class

        Returns:
            Queue pattern to subscribe to
        """
        if not self.per_instrument_queues:
            return base_queue

        # Topics use different addressing
        if base_queue.startswith("/topic/"):
            return base_queue  # Don't transform topics

        # Transform queue patterns for per-instrument routing
        # Pattern: PREFIX.DATA_READY -> PREFIX.*.DATA_READY
        parts = base_queue.split(".")

        if len(parts) >= 2 and parts[-1] == "DATA_READY":
            # Insert wildcard before DATA_READY
            # REDUCTION.DATA_READY -> REDUCTION.*.DATA_READY
            # CATALOG.ONCAT.DATA_READY -> CATALOG.ONCAT.*.DATA_READY
            parts.insert(-1, "*")
            return ".".join(parts)
        elif len(parts) >= 2 and parts[-1] == "CREATE_SCRIPT":
            # REDUCTION.CREATE_SCRIPT -> REDUCTION.*.CREATE_SCRIPT
            parts.insert(-1, "*")
            return ".".join(parts)
        else:
            # Unknown pattern, don't transform
            return base_queue

    def matches_processor_queue(self, actual_queue, base_queue):
        """
        Check if an actual queue name matches a processor's base queue pattern.

        Examples:
          actual_queue="REDUCTION.EQSANS.DATA_READY", base_queue="REDUCTION.DATA_READY" -> True
          actual_queue="CATALOG.CG2.DATA_READY", base_queue="CATALOG.ONCAT.DATA_READY" -> False
          actual_queue="REDUCTION.DATA_READY", base_queue="REDUCTION.DATA_READY" -> True

        Args:
            actual_queue: The actual queue name from the message
            base_queue: The base queue name from the processor class

        Returns:
            True if the actual queue matches the base pattern
        """
        # Exact match (backwards compatibility)
        if actual_queue == base_queue:
            return True

        if not self.per_instrument_queues:
            return False  # Strict matching when per-instrument is disabled

        # Per-instrument pattern matching
        # Convert base_queue to pattern and check if actual_queue matches
        base_parts = base_queue.split(".")
        actual_parts = actual_queue.split(".")

        # Must have one more part than base (the instrument name)
        if len(actual_parts) != len(base_parts) + 1:
            return False

        # Check pattern: base parts must match at same positions
        # REDUCTION.DATA_READY matches REDUCTION.EQSANS.DATA_READY
        # Index: 0=REDUCTION, 1=EQSANS (wildcard), 2=DATA_READY
        for i, base_part in enumerate(base_parts):
            actual_index = i if i == 0 else i + 1  # Skip instrument position
            if actual_parts[actual_index] != base_part:
                return False

        return True

    def log_configuration(self, logger=logging):
        """
        Log the current configuration
        """
        logger.info("Using %s", self.config_file)
        if self.comm_only:
            logger.info("  - Running in COMMUNICATION ONLY mode: no post-processing will be performed")
        logger.info("  - LOCAL execution")
        logger.info("  - Max number of processes: %s", self.max_procs)
        logger.info("  - Per-instrument queues: %s", "ENABLED" if self.per_instrument_queues else "DISABLED")
        logger.info("  - Input queues: %s", self.queues)
        if self.per_instrument_queues:
            logger.info("  - Queue patterns: %s", self.queue_patterns)
        logger.info("  - Installation dir: %s", self.sw_dir)
        logger.info("  - Start script: %s", self.start_script)
        logger.info("  - Task script: %s", self.task_script)
        logger.info("  - Error exceptions: %s", str(self.exceptions))
