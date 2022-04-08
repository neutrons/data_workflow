Docker information
==================

.. toctree::
   :maxdepth: 2

.. note::
   This document is updated, however, it may be good to read the ``docker-compose`` and ``Dockerfile.*`` in the repository themselves for the most up-to-date information.

   This guide assumes that ``docker`` and `docker-compose`_ are present on your system.

Starting and Stopping
---------------------

While docker can be used to start each individual container separately, using ``docker-compose up --buid`` is the preferred method because it starts all services in the correct order.
Pressing ``ctrl-c`` will cleanly shutdown interactive docker.
Pressing ``ctrl-c`` multiple times will kill the running images and leave docker in a somewhat funny state that likely requires running ``docker-compose down`` before starting again
An additional flag ``-d`` can be supplied to run docker in detached mode.

.. note::
   Use ``docker-compose --file <filename>`` to select a different configuration

To start a single image, supply its name as an additional argument to ``docker-compose up``.

To stop all images, including in detached mode, run ``docker-compose down``.

Cleaning docker
---------------

The :doc:`build instructions <build>` suggest using the ``--build`` flag which will build images before starting the containers.
Additionally, one may want to use the ``--force-recreate`` flag to recreate images even if ther configuration and images haven't changed.
The following commands can be used (in this order) to further clean out docker and start with a cleaner state (``-f`` with get rid of the confirmation):

* Use ``docker container prune`` to prune all stopped containers
* [Optional] Use ``docker image prune`` to remove all unused images
* Use ``docker volume prune`` to prune all unused volumes

if explicit pruning does not work, use ``docker system prune -a -f`` to purge all.

Misc
----

1. Several things to keep in mind while running Web monitor via docker:

   * The option ``-d`` will start the web-monitor in the background. Remove it if you want to run the web-monitor in the foreground.
   * The command ``docker container logs CONTAINER_NAME`` will provide the runtime log for given container, where ``CONTAINER_NAME`` can be found via ``docker ps``.
   * Add option ``--build`` to force rebuild the container if the local changes are not reflected in the container.
   * Add option ``--force-recreate`` to recreate all images if ``--build`` does not work.
   * If all fails (e.g. the local changes are not showing up in the runtime instances):
       * stop the instance with ``docker-compose down``.
       * prune caches of images, container and volumes.
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
