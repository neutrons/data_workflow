==============================
Autoreducer configuration file
==============================

The configuration file is located at ``/etc/autoreduce/post_processing.conf`` on each of the
autoreducers. Contact the Linux sysadmins to make changes to the configuration file.

Parameters that may be changed:

- ``"processors"``: List of post-processors – this determines the queues that the autoreducer
  subscribes to. If not defined, the autoreducer will use the default post-processors::

    [
        "oncat_processor.ONCatProcessor",
        "oncat_reduced_processor.ONCatProcessor",
        "create_reduction_script_processor.CreateReductionScriptProcessor",
        "reduction_processor.ReductionProcessor"
    ]

- ``"jobs_per_instrument"``: Limit on the number of concurrent jobs per instrument of the
  autoreducer instance.
