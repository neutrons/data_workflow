How to Build A Local Instance
==============================

.. toctree::
   :maxdepth: 2


Local Development Environment Setup
-----------------------------------

1. Pre-requisites

The web-monitor contains three independent Django applications

    * dasmon: to interface with the data acquisition system (DAS).
    * webmon: user facing web interface, visit the production version at `monitor.sns.gov`_.
    * workflow: backend manager.

and a mocked catalog services.
In order to run a local instance of the web-monitor, you need to have

    * access to `docker`_ engine (preferably with access to a latest version of `docker-compose`_).
    * access to a local instance of `Anaconda`_ for setting up a Python virtual environment.
    * sufficient amount of disk space (~ 10GB) for storing various images.

2. Install dependencies

Install both docker desktop and anaconda following the instructions on the official website.
If possible, install the latest version of docker-compose.
Once all the third-party dependencies are in place, perform the following steps

    * clone the repository, `data_workflow`_ on Github.
    * [optional] purge the cached docker images with ``docker image prune``.
    * [optional] purge the cached containers with ``docker container prune``.
    * [optional] purge the cached volumes with ``docker volume prune``.
    * move to the root of the clone repository to
        * create a virtual environment with ``conda env create --file conda_environment.yml``.
        * activate the virtual environment with ``conda activate webmon``.
        * install the development dependencies with ``conda env update --file conda_development.yml``.

3. Set up environment variables

The website is configured to use the following environment variables to setup authentication services:

    * ``LDAP_SERVER_URI``
    * ``LDAP_DOMAIN_COMPONENT``

Please reach out to the senior developers of `SCSE@ORNL`_ for help with setting up these variables.
Alternatively, the authentication service can be bypassed by setting the following environment variables, which will default the authentication to local Django database only:

    * ``DJANGO_SETTINGS_MODULE='reporting.reporting_app.settings.unittest'``


Running via Docker
------------------

Move to the root of the cloned repository where the docker compose file, ``docker-compose.yml``, is located.
Use the following command to spin up the web-monitor:
   
   * ``docker-compose up -d``

and visit ``localhost`` in your browser.

To stop the instance, use the following command to spin down the web-monitor:

   * ``docker-compose down``

Both commands must be run at the root of the repository where the docker compose file is located.


MISC
------

1. Several things to keep in mind while running Web monitor via docker:

   * The option ``-d`` will start the web-monitor in the background. Remove it if you want to run the web-monitor in the foreground.
   * The command ``docker container logs CONTAINER_NAME`` will provide the runtime log for given container, where ``CONTAINER_NAME`` can be found via ``docker ps``.
   * Add option ``--build`` to force rebuild the container if the local changes are not reflected in the container.
   * Add option ``--force-recreate`` to recreate all images if ``--build`` does not work.
   * If all fails (e.g. the local changes are not showing up in the runtime instances):
       * stop the instance with ``docker-compose down``.
       * prune caches of images, container and volumes.
           * if explicit pruning does not work, use ``docker system prune -a -f`` to purge all.
       * restart the instance with ``docker-compose up -d --build --force-recreate``.

2. If you cannot find web-monitor at ``localhost``, it is possible that the standard http port 80 is used by another application.  Here are two possible solutions:

   * Stop the service running at port 80 and restart the instance.
   * Modify `the port of nginx`_ in the docker compose file to use a different port (e.g. change to ``81:80``).


.. _Anaconda: https://www.anaconda.com/products/distribution
.. _SCSE@ORNL: petersonpf@ornl.gov
.. _data_workflow: https://github.com/neutrons/data_workflow
.. _docker: https://www.docker.com/
.. _docker-compose: https://docs.docker.com/compose/
.. _monitor.sns.gov: https://monitor.sns.gov/
.. _the port of nginx: https://github.com/neutrons/data_workflow/blob/028e4b73d9c7bd85f6d47a452ea641dd2b8d312f/docker-compose.yml#L7
