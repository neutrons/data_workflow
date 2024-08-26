Description of Test Fixtures
============================

.. toctree::
   :maxdepth: 2

The docker files for each test fixture is in the root of the repository with the name ``Dockerfile.<fixturename>``.
The overall design of the test fixture is captured `here <https://code.ornl.gov/sns-hfir-scse/infrastructure/web-monitor/-/tree/next/docs/Design/Design_TestEnv>`_ .
One must be authenticated to view this repository.

``activemq`` fixture is built from `rmohr/activemq <https://github.com/rmohr/docker-activemq>`_ with the configuration from ``src/workflow_app/workflow/icat_activemq.xml``.
It is the activemq broker.


``autoreducer`` fixture runs a copy of `post processing agent <https://github.com/neutrons/post_processing_agent>`_.
This is given a fake filesystem with the contents of ``tests/data`` in the location ``/SNS/`` (at the root level of the filesystem).

`webmonchow fixture <https://webmonchow.readthedocs.io/en/latest/index.html>`_
creates pretend messages associated with runs being saved,
as well as fake process variables (PVs) that the data aquisition would make.

``catalog_process`` fixture is running the script located in ``src/catalog/catalog_process.py`` which responds with the messages in a similar way to how ONCAT would.
The script creates a :py:obj:`~catalog_process.Listener` and responds accordingly.
