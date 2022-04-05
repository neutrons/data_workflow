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
 * `stomp <http://code.google.com/p/stomppy/>`_
 * `django <https://www.djangoproject.com/>`_
 * `MySQLdb <https://sourceforge.net/projects/mysql-python/>`_ if using MySQL
 * `psycopg2 <http://initd.org/psycopg/>`_ if using PostgreSQL

It consists of 3 applications (Workflow Manager, Web Monitor, and DASMON Listener) which are deployed via docker-compose.

Workflow Manager
----------------

Data workflow manager based on ActiveMQ

The database abstraction is done through django.db and the
communication layer is done using stomp

The ``icat_activemq.xml`` file is the ActiveMQ configuration used to set up the
cluster of brokers.

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
DB logging daemon.

The DASMON listener watches for DASMON message sent to ActiveMQ and logs them.
See the ``src/dasmon_app/dasmon_listener/README.md`` file for more details.

**PostgreSQL optimization:**
If using PostgreSQL, you can install the stored procedure in ``reporting/report/sql/stored_procs.sql``.
Those will speed up the run rate and error rate queries.
No change needs to be made to the settings when installing those stored procedures and the application will use them automatically.

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.10054.svg
   :alt: DOI Badge
   :target: https://doi.org/10.5281/zenodo.10054

Setup Dev Environment with docker-compose
-----------------------------------------

During the modernization of WebMon, the developers can setup a local development environment using docker compose.
Here are the recommended steps to setup your dev environment:

* Clone the repository as usual.
* Install ``docker`` and `docker-compose <https://docs.docker.com/compose/install/>`_ if they are not present on your system.
* Cleanup containers, volumes and images from previous run (skip this step if this is the first time)

  * Use ``docker container prune`` to prune all stopped containers
  * Use ``docker volume prune`` to prune all volumes
  * [Optional] Use ``docker image prune`` to remove all images

* Move to the directory that contains ``docker-compose.yml`` (the root of repo)
* Set the required environment variables for LDAP

  * ``export LDAP_SERVER_URI=.``
  * ``export LDAP_DOMAIN_COMPONENT=.``

* Spin up the rest of the system with (``--build`` may be unnecessary)

  * ``docker-compose up --build``
  * Keep this running in your terminal so that you can see the real time log from all containers
  * ``--build`` will ensure any local changes will be updated in containers at the cost of increasing the startup time

* Open a browser and go to http://localhost to see the login page
* Log in with the newly added super user (defined through ``DATABASE_USER`` and ``DATABASE_PASS`` variables in ``.env`` file)

  * user name: ``postgres``
  * password: ``postgres``

* After editing the source code, you


Running unit tests
------------------

* ``conda env create --file conda_environment.yml`` or ``conda env update --file conda_environment.yml`` if the environment already exists
* ``conda activate webmon``
* ``conda env update --file conda_development.yml``
* ``python -m pytest src``
