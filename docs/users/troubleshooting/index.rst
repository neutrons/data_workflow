===============
Troubleshooting
===============

Autoreduction
-------------

- Check that all autoreduction services are up:
  https://monitor.sns.gov/dasmon/common/diagnostics/
- Examine the autoreduction logs on the analysis cluster:
  ``/<facility>/<instrument>/IPTS-XXXX/shared/autoreduce/reduction_log/``, see also
  :ref:`autoreduction_report`.
- Examine the autoreducers logs on the individual autoreducers at
  ``/var/log/SNS_applications/postprocessing.log``.
- Verify the configuration of the autoreduction workflow at:
  https://monitor.sns.gov/database/report/task/.

Database view
-------------
Users with admin privileges can open the Django admin interface at
https://monitor.sns.gov/database/ to view the database tables. Log tables, e.g. "Run status", may
be useful for troubleshooting.

.. toctree::
   :maxdepth: 2
   :caption: Topics with more detail:

   Autoreduction_report
   Autoreducer_configuration_file
   Message_broker
