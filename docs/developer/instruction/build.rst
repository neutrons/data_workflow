Developing in a Local Environment
=================================

.. toctree::
   :maxdepth: 2

.. note::
   This document is updated, however, it may be good to read the `continuous integration <https://github.com/neutrons/data_workflow/tree/next/.github/workflows>`_ scripts as well.

Requirements
------------

* PostgreSQL 17 or higher
* Python 3.11
* Docker and Docker Compose (for local development)

Dependencies between services
-----------------------------

The services making up the infrastructure of Web Monitor have dependencies.
The diagram below shows the dependencies for a local deployment guaranteeing that
the application will run _and_ that both unit and system tests will pass.

``service1`` --> ``service2`` is to be read as ``service1`` depends on ``service2``.
For instance, ``webmonchow`` depends on ``db``.

.. image:: ../images/local_deployment_dependence_graph.png
   :width: 600px
   :align: center
   :alt: services dependence graph


Description of available Django settings
----------------------------------------
Settings are split according to different target environments,
which can be roughly divided into *local* and *remote* environments.
A settings is selected by specifying variable ``DJANGO_SETTINGS_MODULE``

**Local Environments:**
    * ``reporting.reporting_app.settings.unittest`` for running outside of docker, in the pixi environment
    * ``reporting.reporting_app.settings.develop`` for local docker containers.
      This can be connected to production ldap server in a read only mode and will ignore TLS errors.
    * ``reporting.reporting_app.settings.envtest`` for running system tests with docker images.

**Remote Environments:**
    * ``reporting.reporting_app.settings.prod`` for the testing and production environments deployed by
      the CI/CD pipeline of https://code.ornl.gov/sns-hfir-scse/deployments/web-monitor-deploy.


Running static analysis
-----------------------

This repository uses `pre-commit framework <https://pre-commit.com/>`_ to run the static analysis checks.
After installing pre-commit the checks can be run using

.. code-block:: shell

   pre-commit run --all-files

Python package configuration
-----------------------------

This project contains three separate Python packages (dasmon_app, webmon_app, and workflow_app),
each with its own ``pyproject.toml`` file following modern Python packaging standards (PEP 518 and PEP 621).
The configuration includes:

* Package metadata (name, version, description, authors, license)
* Console script entry points for command-line tools
* Package data specifications (SQL files, templates, static assets)
* Build system configuration using setuptools
* Test dependencies

Each package can be built independently using:

.. code-block:: shell

   pixi run wheel-dasmon   # Build dasmon package
   pixi run wheel-webmon   # Build webmon package
   pixi run wheel-workflow # Build workflow package
   pixi run wheel-all      # Build all three packages

The built wheels are stored in each package's ``dist/`` directory.
In the Docker containers, wheels are built automatically at image build time via multistage builds —
no manual pre-build step is required before ``docker compose up --build``.

Running unit tests
------------------

The unit tests exist next to the code it is testing.
They are run inside a pixi environment with configuration defined in the root-level ``pyproject.toml``.
This is based on what is run in `.github/workflow/ci.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/ci.yml>`_

.. code-block:: shell

   pixi run unittests

Running system tests
--------------------

The system test are run via `.github/workflow/systemtests.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/systemtests.yml>`_ .

.. code-block:: shell

   pixi run test-data
   pixi run ssl
   LDAP_SERVER_URI=. LDAP_DOMAIN_COMPONENT=. DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.envtest docker compose up --build

Wait for a time for everything to get up and running.
This is normally noted by seeing a collection of worker threads starting.
Once started tests can be run via

.. code-block:: shell

   pixi run systemtests

Building a local deployment
---------------------------

Most of the shell commands used when working in the developer setup (a.k.a "localdev")
are encapsulated in ``pixi`` tasks. Run ``pixi task list`` for a list of available tasks.

When starting from scratch, open a shell where the following secret environment variables have
been initialized:

.. code-block:: shell

   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.develop
   GENERAL_USER_USERNAME=GeneralUser
   GENERAL_USER_PASSWORD=GeneralUser
   LDAP_SERVER_URI=*****
   LDAP_USER_DN_TEMPLATE=*****
   LDAP_DOMAIN_COMPONENT=*****
   CATALOG_URL=*****
   CATALOG_API_TOKEN=*****

It is recommended to store these variables in an ``.envrc`` file and manage their loading/unloading
into the shell with the `direnv <direnv/>`_ command-line utility.

Secret Variables
++++++++++++++++
The environment variables ``LDAP_SERVER_URI`` and ``LDAP_DOMAIN_COMPONENT`` are shown above with no-op values.
Senior developers can provide the values to use,
then the developer setup can work with Neutron Scattering Division's (NSD) LDAP instance.

The environment variables ``CATALOG_URL`` and ``CATALOG_API_TOKEN``
can be set to allow run metadata to be retrieved
from `ONCat <https://oncat.ornl.gov>`_.

Special users
+++++++++++++
While one can connect to the production LDAP, in a developer environment there are listed below as username:password

* ``GeneralUser`` : ``GeneralUser`` has permissions to pages similar to a general beamline users.
  The username and password can be set using the ``GENERAL_USER_USERNAME`` and ``GENERAL_USER_PASSWORD`` environment variables.
  The credentials are stored in ``unittest.py`` settings file
* ``InstrumentScientist`` : ``InstrumentScientist`` has permissions similar to an instrument scientist


After setting the environment variables, run the following ``pixi`` tasks in the shell:

.. code-block:: shell

   pixi run all         # create: fake SNS data; self-signed SSL certificates; python packages
   pixi run localdev-up # build all the services

The site is served at http://localhost by default.

Porting changes in the source code to the local deployment
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
The apps are actually served in the local deployment from python wheels.
Thus, after changing the source code of the apps,
it is necessary to rebuild the python wheels and restart the services.

1. stop the running containers
2. recreate the python wheel(s) if the source code of the apps has changed
3. rebuild the services

Stop the running containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Stoping and deleting the running containers as well as deleting the images and docker volumes:

.. code-block:: shell

   docker compose down --volumes

this command will delete the database. Omit ``--volumes`` if preservation of the database is desired.

Alternatively, do **Ctrl-C** in the terminal where you ran ``pixi run localdev-up`` or ``docker compose up --build``.

Rebuild after source changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
With multistage Docker builds, wheels are built automatically inside Docker at image build time.
After changing the source code of an app, rebuild only its service:

.. code-block:: shell

   pixi run build-service --service=webmon   # or dasmon, workflow

To rebuild all services:

.. code-block:: shell

   pixi run localdev-up

This runs ``docker compose up --build`` using settings in ``docker-compose.yml``.
Local wheel builds can still be triggered manually (e.g. for inspection) with
``pixi run wheel-dasmon`` etc., but they are not required before starting the containers.

More information on docker commands for this project can be found :doc:`here <docker>`.

Uploading a database dump
+++++++++++++++++++++++++

Pixi task ``localdev-dbup`` contains the shell command to load the
database dump and start the service. Assuming that:

- the full path to the dump file  is ``./database_dump_file.sql``:
- the current working directory is the root of the source tree (containing file ``.env``):

.. code-block::

   $> dbdumpfile=./database_dump_file.sql DATABASE_PASS=$(dotenv get DATABASE_PASS) pixi run localdev-dbup

Task ``localdev-dbup`` sets ``LOAD_INITIAL_DATA="false"``, thus preventing loading the default
database dump (file "db_init.json")
