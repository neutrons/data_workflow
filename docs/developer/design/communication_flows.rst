.. _communication_flows:

ActiveMQ Communication Flows
============================

.. contents:: :local:

Autoreducers
------------

Run post-processing
...................

The sequence diagram below describes the communication flow as a run gets post-processed.
The post-processing workflow is triggered when the Translation Service has finished translating the
data stream to NeXus and sends a message on the queue ``POSTPROCESS.DATA_READY`` specifying the
instrument, IPTS, run number and location of the NeXus file.

The post-processing workflow for the instrument is configurable in the database table
``report_task``.
The diagram shows the three post-processing steps that are available: autoreduction, cataloging of
raw data in `ONCat <https://oncat.ornl.gov/>`_ and cataloging of reduced data in
`ONCat <https://oncat.ornl.gov/>`_.

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
        Autoreducer->>Autoreducer: run reduction
        Autoreducer->>Workflow Manager: REDUCTION.COMPLETE
        Workflow Manager->>Autoreducer: REDUCTION_CATALOG.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.STARTED
        Autoreducer->>ONCat: pyoncat
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.COMPLETE

..
    .. mermaid::

        sequenceDiagram
            participant Translation Service
            participant Workflow Manager
            participant Autoreducer

            Translation Service->>Workflow Manager: POSTPROCESS.DATA_READY
            opt Cataloging
                Workflow Manager->>Autoreducer: CATALOG.ONCAT.DATA_READY
                Autoreducer->>Workflow Manager: CATALOG.ONCAT.STARTED
                Note over Autoreducer: Ingest in ONCat
                Autoreducer->>Workflow Manager: CATALOG.ONCAT.COMPLETE
            end
            opt Autoreduction
                Workflow Manager->>Autoreducer: REDUCTION.DATA_READY
                Autoreducer->>Workflow Manager: REDUCTION.STARTED
                Note over Autoreducer: Execute autoreduction script
                Autoreducer->>Workflow Manager: REDUCTION.COMPLETE
            end
            opt Reduced data cataloging
                Workflow Manager->>Autoreducer: REDUCTION_CATALOG.DATA_READY
                Autoreducer->>Workflow Manager: REDUCTION_CATALOG.STARTED
                Note over Autoreducer: Ingest in ONCat
                Autoreducer->>Workflow Manager: REDUCTION_CATALOG.COMPLETE
            end


Configuring the autoreduction
.............................

In addition to run post-processing, the autoreducers handle updating instrument reduction script
parameters for instruments that have implemented
:doc:`autoreduction parameter configuration<../instruction/autoreduction>` at
`monitor.sns.gov/reduction/<instrument>/ <https://monitor.sns.gov/reduction/cncs/>`_.

.. mermaid::

    sequenceDiagram
        actor Instrument Scientist
        participant WebMon
        participant Autoreducer
        participant HFIR/SNS File archive

        Instrument Scientist->>WebMon: Submit form with parameter values
        WebMon->>Autoreducer: REDUCTION.CREATE_SCRIPT
        Autoreducer->>HFIR/SNS File archive: Update instrument reduction script

DASMON
------
DASMON, from Data Acquisition (DAQ) System Monitor, provides instrument status and process variable
(PV) updates from the beamlines to WebMon. DASMON connects to the WebMon message broker to pass
status information, for example the current run number and count rate, to Dasmon listener. Due to
the high volume of PV updates, DASMON writes PV:s directly to the PostgreSQL database.

.. mermaid::

    sequenceDiagram
        participant DASMON
        participant Dasmon listener
        participant Workflow DB
        DASMON->>Workflow DB: PV update
        DASMON->>Dasmon listener: Instrument status
        DASMON->>Workflow DB: Instrument status

Dasmon listener
---------------

Stream Management Service (SMS)
...............................

.. mermaid::

    sequenceDiagram
        participant SMS
        participant Dasmon listener
        participant Workflow DB
        SMS->>Dasmon listener: Run started
        Dasmon listener->>Workflow DB: Create new run
        SMS->>Dasmon listener: Run stopped
        SMS->>Dasmon listener: Translation succeeded

Heartbeats from services
........................

Dasmon listener subscribes to heartbeats from the other services. There is a mechanism for alerting
admins by email when a service has missed heartbeats (needs to be verified that this still works).

..
    .. mermaid::

        sequenceDiagram
            participant Other services
            participant Dasmon listener
            participant Workflow DB
            actor Subscribed users
            loop Every N s
                Other services->>Dasmon listener: Heartbeat
                Dasmon listener->>Workflow DB: Status update
            end
            opt Service has 3 missed heartbeats
                Dasmon listener->>Subscribed users: Email
            end


.. mermaid::

    flowchart LR
        SMS["SMS (per beamline)"]
        PVSD["PVSD (per beamline)"]
        DASMON["DASMON (per beamline)"]
        STC
        Autoreducers
        DasmonListener
        WorkflowDB[(DB)]
        SMS-->|heartbeat|DasmonListener
        PVSD-->|heartbeat|DasmonListener
        DASMON-->|heartbeat|DasmonListener
        STC-->|heartbeat|DasmonListener
        Autoreducers-->|heartbeat|DasmonListener
        WorkflowManager-->|heartbeat|DasmonListener
        DasmonListener-->|heartbeat|DasmonListener
        DasmonListener-->WorkflowDB
        DasmonListener-.->|if missed 3 heartbeats|InstrumentScientist

Live Data Server
----------------------------------------

WebMon has two modes of interaction with Live Data Server: publish (save) plots to the Live Data
Server database and display (fetch) plots from the database.

Publish to Live Data Server from autoreduction script
.....................................................

The instrument-specific autoreduction script can optionally publish plots (in either JSON format
or HTML div) to Live Data Server.

.. mermaid::

    sequenceDiagram
        participant WebMon
        participant Autoreducer
        participant Live Data Server

        WebMon->>Autoreducer: REDUCTION.DATA_READY
        opt Publish plot
            Autoreducer->>Live Data Server: publish_plot
        end

Publish to Live Data Server from live data stream
.................................................

Livereduce (https://github.com/mantidproject/livereduce/) allows scientists to reduce
data from an ongoing experiment, i.e. before translation to NeXus, by connecting to the live data
stream from the Stream Management Service (SMS). The instrument-specific processing
script can make the results available in WebMon by publishing plots to Live Data Server.

.. mermaid::

    sequenceDiagram
        participant SMS
        participant Livereduce
        participant Live Data Server

        SMS->>Livereduce: data stream
        loop Every N minutes
            Livereduce->>Livereduce: run processing script
            Livereduce->>Live Data Server: publish plot
        end


Display plot from Live Data Server
................................

Run overview pages (``monitor.sns.gov/report/<instrument>/<run number>/``) will query the Live
Data Server for a plot for that instrument and run number and display it if available.

.. mermaid::

    sequenceDiagram
        participant WebMon
        participant Live Data Server

        WebMon->>Live Data Server: HTTP GET
        loop Every 60 s
            WebMon->>Live Data Server: HTTP GET
        end
