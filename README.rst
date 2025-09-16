.. image:: https://readthedocs.org/projects/data-workflow/badge/?version=latest
   :target: https://data-workflow.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://github.com/neutrons/data_workflow/actions/workflows/ci.yml/badge.svg?branch=next
   :alt: CI
   :target: https://github.com/neutrons/data_workflow/actions/workflows/ci.yml?query=branch:next
.. image:: https://codecov.io/gh/neutrons/data_workflow/branch/next/graph/badge.svg?token=q1f07RUI88
   :alt: codecov
   :target: https://codecov.io/gh/neutrons/data_workflow
.. image:: https://bestpractices.coreinfrastructure.org/projects/5504/badge
   :alt: CII Best Practices
   :target: https://bestpractices.coreinfrastructure.org/projects/5504

Data Workflow Manager
---------------------

SNS data workflow manager and reporting app

Dependencies:
 * `stomp <https://github.com/jasonrbriggs/stomp.py>`_
 * `django <https://www.djangoproject.com/>`_
 * `MySQLdb <https://sourceforge.net/projects/mysql-python/>`_ if using MySQL
 * `psycopg2 <https://www.psycopg.org/>`_ if using PostgreSQL

It consists of 3 applications (Workflow Manager, Web Monitor, and DASMON Listener) which are deployed via docker compose.

Workflow Manager
----------------

Data workflow manager based on  ActiveMQ

The database abstraction is done through django.db and the communication layer is done using stomp.

The ``icat_activemq.xml`` file is the ActiveMQ configuration used to set up the cluster of brokers.

Use ``sns_post_processing.py`` to start the workflow manager.

Use ``test/test_consumer.py`` to simulate the worker nodes.

Web Monitor
-----------
Reporting application for the workflow manager.
The reporting app is built using django.
It connects to the reporting database used by the workflow manager.
Look at the ``docker-compose.yml`` to see how to configure and run it.

DASMON listener
---------------
DB logging.

The DASMON listener watches for DASMON message sent to ActiveMQ and logs them.
See the ``src/dasmon_app/dasmon_listener/README.md`` file for more details.

**PostgreSQL optimization:**
If using PostgreSQL, you can install the stored procedure in ``reporting/report/sql/stored_procs.sql``.
Those will speed up the run rate and error rate queries.
No change needs to be made to the settings when installing those stored procedures and the application will use them automatically.

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.10054.svg
   :alt: DOI Badge
   :target: https://doi.org/10.5281/zenodo.10054

Developer's Entry Point
-----------------------
Start at the Developer's documentation. This requires building the docs:

.. code-block:: bash

   $ pixi shell
   $ make docs
