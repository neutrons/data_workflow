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
They are run inside a conda enviroment and pointing at the correct directory with the configuration inside the root-level ``setup.cfg``.
Replace ``conda`` with ``mamba`` for the faster dependency resolver.
This is based on what is run in `.github/workflow/ci.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/ci.yml>`_

.. code-block:: shell

   conda env create --file conda_environment.yml
   conda activate webmon
   conda env update --file conda_development.yml
   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.unittest \
      python -m pytest src

If the environment already exists ``conda_enviroment.yml`` can be used to update it as well.

Running system test
-------------------

The system test are run via `.github/workflow/system.yml <https://github.com/neutrons/data_workflow/blob/next/.github/workflows/system.yml>`_ .

.. code-block:: shell

   make all # wheels and test data
   LDAP_SERVER_URI=. LDAP_DOMAIN_COMPONENT=. docker-compose up --build

Wait for a time for everyting to get up and running.
This is normally noted by seeing a collection of worker threads starting.
Once started thests can be run via

.. code-block:: shell

   DJANGO_SETTINGS_MODULE=reporting.reporting_app.settings.unittest \
      python -m pytest tests

Developer setup
---------------
This can be done the same as running the system tests as far as creating artifacts and starting docker-compose, but does not require running pytest.
The site is served at http://localhost by default.
More information on docker in this project is :doc:`here <docker>`.

Description of settings
-----------------------
The settings are split into a couple of bundled options that can be selected by specifying ``DJANGO_SETTINGS_MODULE``

    * ``reporting.reporting_app.settings.unittest`` for running outside of docker in the conda environment
    * ``reporting.reporting_app.settings.develop`` for local docker containers. This can be connected to production ldap server in a read only mode and will ignore TLS errors
    * ``reporting.reporting_app.settings.envtest`` for the remote testing environment
    * ``reporting.reporting_app.settings.prod`` for production

The environment variables ``LDAP_SERVER_URI`` and ``LDAP_DOMAIN_COMPONENT`` are shown above with no-op values.
Senior developers can provide the values to use, then the developer setup can work with Neutron Scattering Division's (NSD) LDAP instance.

Special users
-------------

While one can connect to the production LDAP, in a developer environment there are listed below as username:password

* ``GeneralUser`` : ``GeneralUser`` has permissions to pages similar to a general beamline users.
  The username and password can be set using the ``GENERAL_USER_USERNAME`` and ``GENERAL_USER_PASSWORD`` environment variables.
  The credentials are stored in ``unittest.py`` settings file
* ``InstrumentScientist`` : ``InstrumentScientist`` has permissions similar to an instrument scientist
