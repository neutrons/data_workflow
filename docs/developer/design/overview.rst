Design Overview
===============

ActiveMQ Communication Flow
---------------------------

This sequence diagram describes the communication flow through the ActiveMQ message broker as a run
gets processed in WebMon.

Note that the post-processing workflow is configurable in the database table ``Task`` - the
sequence presented here is representative for the majority of the instruments.

.. mermaid::

    sequenceDiagram
        participant Translation Service
        participant Workflow Manager
        participant Autoreducer
        participant ONCat


        Translation Service->>Workflow Manager: POSTPROCESS.DATA_READY
        Workflow Manager->>Autoreducer: CATALOG.ONCAT.DATA_READY
        Autoreducer->>Workflow Manager: CATALOG.ONCAT.STARTED
        Autoreducer->>ONCat: pyoncat
        Autoreducer->>Workflow Manager: CATALOG.ONCAT.COMPLETE
        Workflow Manager->>Autoreducer: REDUCTION.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION.STARTED
        Autoreducer->>Workflow Manager: REDUCTION.COMPLETE
        Workflow Manager->>Autoreducer: REDUCTION_CATALOG.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.STARTED
        Autoreducer->>ONCat: pyoncat
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.COMPLETE


.. mermaid::

    sequenceDiagram
        participant Translation Service
        participant Workflow Manager
        participant Autoreducer
        participant ONCat


        Translation Service->>Workflow Manager: POSTPROCESS.DATA_READY
        Workflow Manager->>Autoreducer: CATALOG.ONCAT.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION.STARTED
        Autoreducer->>Workflow Manager: REDUCTION.COMPLETE


.. list-table:: Reduction Plan - Main Fields
   :widths: 20 20 20 20 20
   :header-rows: 1

   * - Field
     - Type
     - Value Origin
     - Additional validation
     - Mandatory
   * - Reduction Plan
     - String
     -
     - filepath usage
     - yes
   * - Instrument
     - String
     - predefined choices from available instrument
     -
     - yes
   * - IPTS
     - Integer
     -
     - valid/existing filepath
     - yes
   * - Run Ranges
     - Comma-separated numbers and number ranges
     -
     - valid/existing filepath
     - yes
   * - Wavelength
     - Float
     - default value from instrument configuration
     - positive
     - yes
   * - Grouping
     - String
     - predefined choices from instrument configuration
     -
     - yes



WebMon interaction with Live Data Server
----------------------------------------

WebMon has two modes of interaction with Live Data Server: publish (save) plots to the Live Data
Server database and display (fetch) plots from the database.

Publish to Live Data Server
...........................

The instrument-specific autoreduction script can optionally publish plots (in either JSON format
or HTML div) to Live Data Server.

.. mermaid::

    sequenceDiagram
        participant WebMon
        participant Autoreducer
        participant Live Data Server

        WebMon->>Autoreducer: REDUCTION.DATA_READY
        Autoreducer->>Live Data Server: publish_plot
        Note over Live Data Server: Store plot in DB

Fetch plot from Live Data Server
................................

Run overview pages (monitor.sns.gov/report/<instrument>/<run number>/) will query the Live
Data Server for a plot for that instrument and run number and display it if available.

.. mermaid::

    sequenceDiagram
        participant WebMon
        participant Live Data Server

        WebMon->>Live Data Server: HTTP GET
        loop Every 60 s
            WebMon->>Live Data Server: HTTP GET
        end
