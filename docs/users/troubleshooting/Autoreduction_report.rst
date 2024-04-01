.. _autoreduction_report:

====================
Autoreduction report
====================

The script
`ar_report.py <https://github.com/neutrons/post_processing_agent/blob/main/scripts/ar_report.py>`_
can be used to extract and aggregate information about autoreduction from the reduction logs, e.g.
which host the autoreduction ran on and how long it took.

Example of creating a report for one run::

    python ar_report.py /HFIR/HB2C/IPTS-31640/nexus/HB2C_1238907.nxs.h5 out_ar_report/

Example of creating a report for all runs of one IPTS::

    python ar_report.py /HFIR/HB2C/IPTS-31640/ out_ar_report/

Example output:

.. csv-table::
   :file: HB2C-IPTS-31640.csv
   :header-rows: 1

Note that the last column ``meas-redux`` of ``HB2C_1238907`` shows that the autoreduction time was
longer than the measurement time for this run.
