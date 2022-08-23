How to Build A Local Instance
==============================

.. toctree::
   :maxdepth: 2

.. note::
   This document is updated, however, it may be good to read the `continuous integration <https://github.com/neutrons/data_workflow/tree/next/.github/workflows>`_ scripts as well.

Running static analysis
-----------------------

This repository uses `pre-commit framework <https://pre-commit.com/>`_ to run the static analysis checks.
After installing pre-commit the checks can be run using

.. code-block:: shell

   pre-commit run --all-files

Running unit tests
------------------

The unit tests exist next to the code it is testing.
They are run inside a conda environment and pointing at the correct directory with the configuration inside the root-level ``setup.cfg``.
Replace ``conda`` with ``mamba`` for the faster dependency resolver.
This is based on what is run in `.github/workflow/ci.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/ci.yml>`_

.. code-block:: shell

   make create/conda  # substitute with "create/mamba" when using mamba
   conda activate webmon
   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.unittest \
      python -m pytest src

If the environment already exists, ``conda_environment.yml`` can be used to update it as well.

.. code-block:: shell

   conda activate webmon
   conda env update --file conda_development.yml

Running system test
-------------------

The system test are run via `.github/workflow/system.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/system.yml>`_ .

.. code-block:: shell

   make all # wheels and test data
   LDAP_SERVER_URI=. LDAP_DOMAIN_COMPONENT=. docker-compose up --build

Wait for a time for everything to get up and running.
This is normally noted by seeing a collection of worker threads starting.
Once started tests can be run via

.. code-block:: shell

   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.envtest \
      python -m pytest tests

Setup and Deployment for Development
------------------------------------

Most of the shell commands used when working in the developer setup (a.k.a "localdev")
are encapsulated in `make` targets. Type `make help` for a list of `make` targets
and a brief description.

When starting for scratch, open a shell where the following secret environment variables have
been initialized:

.. code-block:: shell

   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.develop
   GENERAL_USER_USERNAME=GeneralUser
   GENERAL_USER_PASSWORD=GeneralUser
   LDAP_SERVER_URI=*****
   LDAP_USER_DN_TEMPLATE=*****
   LDAP_DOMAIN_COMPONENT=*****
   CATALOG_URL=*****
   CATALOG_ID=*****
   CATALOG_SECRET=*****

It is recommended to store these variables in an `.envrc` file and manage their loading/unloading
into the shell with the `direnv <direnv/>`_ command-line utility.

Description of settings
+++++++++++++++++++++++
The settings are split into a couple of bundled options that can be selected by specifying ``DJANGO_SETTINGS_MODULE``

    * ``reporting.reporting_app.settings.unittest`` for running outside of docker in the conda environment
    * ``reporting.reporting_app.settings.develop`` for local docker containers. This can be connected to production ldap server in a read only mode and will ignore TLS errors
    * ``reporting.reporting_app.settings.envtest`` for the remote testing environment
    * ``reporting.reporting_app.settings.prod`` for production

The environment variables ``LDAP_SERVER_URI`` and ``LDAP_DOMAIN_COMPONENT`` are shown above with no-op values.
Senior developers can provide the values to use, then the developer setup can work with Neutron Scattering Division's (NSD) LDAP instance.

The environment variables ``CATALOG_URL``, ``CATALOG_ID`` and
``CATALOG_SECRET`` can be set to allow run metadata to be retrieved
from `ONCat <https://oncat.ornl.gov>`_.

Special users
+++++++++++++
While one can connect to the production LDAP, in a developer environment there are listed below as username:password

* ``GeneralUser`` : ``GeneralUser`` has permissions to pages similar to a general beamline users.
  The username and password can be set using the ``GENERAL_USER_USERNAME`` and ``GENERAL_USER_PASSWORD`` environment variables.
  The credentials are stored in ``unittest.py`` settings file
* ``InstrumentScientist`` : ``InstrumentScientist`` has permissions similar to an instrument scientist


After setting the environment variables, run the following `make` targets in the shell:

.. code-block:: shell

   make conda/create
   make wheel/all  # create python packages for dasmon, webmon, and workflow
   make SNSdata.tar.gz  # create fake SNS data for testing
   make localdev/up  # build all the services

The site is served at http://localhost by default.

After making changes to the source code, it is necessary to:

1. stop the running containers
2. recreate the python wheel(s) if the source code of the apps has changed
3. rebuild the images

Stop the Running Containers
+++++++++++++++++++++++++++
Stoping and deleting the running containers as well as deleting the images and docker volumes:

.. code-block:: shell

   docker-compose down --volumes

this command will delete the database. Omit `--volumes` if preservation of the database is desired.

Recreate the Python Wheels
++++++++++++++++++++++++++
The selected format to inject `dasmon`, `webmon`, and `worflow` apps into their
corresponding services is python wheels, thus any changes for the python
source code requires rebuilding the python wheel(s).

For instance, if the source code of `dasmon` is changed, run at this
point `make wheel/dasmon` to rebuild the `dasmon` wheel.

If necessary, delete all existing wheels with `make wheel/clean`

Rebuild the Images
++++++++++++++++++
Run `make localdev/up`. This `make` target builds the services
with command `docker-compose up --build` using settings in `docker-compose.yml`.

More information on docker commands for this project can be found :doc:`here <docker>`.

Uploading a Database Dump
+++++++++++++++++++++++++

Make target `localdev/dbup` contains the shell command to load the
database dump and start the service. Assuming that:

- we started the `webmon` Conda environment
- the full path to the dump file  is `./database_dump_file.sql`:
- the current working directory is the root of the source tree (containing file `.env`):

.. code-block::

   (webmon) $> dbdumpfile=./database_dump_file.sql make DATABASE_PASS=$(dotenv get DATABASE_PASS) localdev/dbup

Target `localdev/dbup` sets `LOAD_INITIAL_DATA="false"`, thus preventing loading the default
database dump (file "db_init.json")
