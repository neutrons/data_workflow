Developer documentation
=======================

Developer Guide
---------------

.. toctree::
   :maxdepth: 1

   instruction/build
   instruction/test_fixture
   instruction/docker
   instruction/autoreduction
   instruction/contribute
   instruction/manual_testing
   instruction/deployment

Modules
-------

The web-monitor contains three independent Django applications

    * :py:mod:`dasmon_listener`: to interface with the data acquisition system (DAS).
    * :py:mod:`webmon <reporting>`: user facing web interface, visit the production version at `monitor.sns.gov`_.
    * :py:mod:`workflow`: backend manager.

and a mocked catalog services.

.. toctree::
   :maxdepth: 1

   dasmon/modules
   webmon/modules
   workflow/modules
   catalog/modules

.. _monitor.sns.gov: https://monitor.sns.gov/

Services
--------

The components making up the infrastructure of Web Monitor have dependencies.
In the diagram below `service1` --> `service2` is to be read as `service1` depends on `service2`.
For instance, `amq_pv_gen` depends on `db`.

.. image:: images/services_dependence_graph.png
    :width: 600px
    :align: center
    :alt: services dependence graph

Related software
----------------

* `post_processing_agent <https://github.com/neutrons/post_processing_agent/>`_ is the system that runs on the autoreducer nodes
* `live_data_server <https://github.com/neutrons/live_data_server>`_ is the system that contains database for holding the plots/divs produced by live reduction and autoreduction
* `livereduce <https://github.com/mantidproject/livereduce>`_ is the ``sysctl`` daemon that runs on instrument computers and generates plots of the active acquisition
