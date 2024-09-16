.. _communication_flows:

Communication Flows
===================

This section presents communication sequences organized by WebMon functionality.

.. contents:: :local:

Experiment monitoring
---------------------

Instrument status and PV updates
................................

DASMON, from Data Acquisition (DAQ) System Monitor, provides instrument status and process variable
(PV) updates from the beamlines to WebMon. DASMON connects to the WebMon message broker to pass
status information, for example the current run number and count rate, to Dasmon listener. Due to
the high volume of PV updates, DASMON writes PV:s directly to the PostgreSQL database.

.. mermaid::

    sequenceDiagram
        participant DASMON
        participant Dasmon listener
        participant Workflow DB
        par
            DASMON->>Workflow DB: PV update
        and
            DASMON->>Dasmon listener: Instrument status
            Dasmon listener->>Workflow DB: Instrument status
        end

Run status updates
..................

The Stream Management Service (SMS) posts messages on the queue ``APP.SMS`` at run start, run stop
and when the Streaming Translation Client (STC) completes translation to NeXus.

.. mermaid::

    sequenceDiagram
        participant SMS
        participant Dasmon listener
        participant Workflow DB
        SMS->>Dasmon listener: Run started
        Dasmon listener->>Workflow DB: Add new data run
        Dasmon listener->>Workflow DB: Run status
        SMS->>Dasmon listener: Run stopped
        Dasmon listener->>Workflow DB: Run status
        SMS->>Dasmon listener: Translation succeeded
        Dasmon listener->>Workflow DB: Run status


Experiment data post-processing
-------------------------------

Autoreduction and cataloging
............................

The sequence diagram below describes the communication flow as a run gets post-processed.
The post-processing workflow is triggered when the Streaming Translation Client (STC) has finished
translating the data stream to NeXus and sends a message on the queue ``POSTPROCESS.DATA_READY``
specifying the instrument, IPTS, run number and location of the NeXus file.

The post-processing workflow for the instrument is configurable in the database table
``report_task``.
The diagram shows the three post-processing steps that are available: autoreduction, cataloging of
raw data in `ONCat <https://oncat.ornl.gov/>`_ and cataloging of reduced data in
`ONCat <https://oncat.ornl.gov/>`_.
Note that the sequence in the diagram is one possible workflow, but there are variations in the
configured sequence and the steps included depending on the instrument.

.. mermaid::

    sequenceDiagram
        participant STC
        participant Workflow Manager
        participant Autoreducer
        participant ONCat
        participant HFIR/SNS File Archive

        STC->>Workflow Manager: POSTPROCESS.DATA_READY
        Workflow Manager->>Autoreducer: CATALOG.ONCAT.DATA_READY
        Autoreducer->>Workflow Manager: CATALOG.ONCAT.STARTED
        Autoreducer->>ONCat: pyoncat
        Autoreducer->>Workflow Manager: CATALOG.ONCAT.COMPLETE
        Workflow Manager->>Autoreducer: REDUCTION.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION.STARTED
        Autoreducer->>HFIR/SNS File Archive: reduced data, reduction log
        Autoreducer->>Workflow Manager: REDUCTION.COMPLETE
        Workflow Manager->>Autoreducer: REDUCTION_CATALOG.DATA_READY
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.STARTED
        Autoreducer->>ONCat: pyoncat
        Autoreducer->>Workflow Manager: REDUCTION_CATALOG.COMPLETE

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

Live data visualization
--------------------------

Live Data Server (https://github.com/neutrons/live_data_server) is a service that serves plots to
the WebMon frontend. It provides a REST API with endpoints to create/update to and retrieve plots
from the Live Data Server database.

Publish to Live Data Server from live data stream
.................................................

Livereduce (https://github.com/mantidproject/livereduce/) allows scientists to reduce
data from an ongoing experiment, i.e. before translation to NeXus, by connecting to the live data
stream from the Stream Management Service (SMS). The instrument-specific livereduce processing
script can make the results available in WebMon by publishing plots to Live Data Server.

.. mermaid::

    sequenceDiagram
        participant SMS
        participant Livereduce
        participant Live Data Server

        SMS->>Livereduce: data stream
        loop Every N minutes
            Livereduce->>Livereduce: run processing script
            Livereduce->>Live Data Server: HTTP POST
        end

Publish to Live Data Server from autoreduction script
.....................................................

The instrument-specific autoreduction script can include a step to publish plots (in either JSON
format or HTML div) to Live Data Server. The Post-processing Agent repository includes some
convenience functions for generating and publishing plots in `publish_plot.py
<https://github.com/neutrons/post_processing_agent/blob/main/postprocessing/publish_plot.py>`_.

.. mermaid::

    sequenceDiagram
        participant Workflow Manager
        participant Autoreducer
        participant Live Data Server

        Workflow Manager->>Autoreducer: REDUCTION.DATA_READY
        opt Publish plot
            Autoreducer->>Live Data Server: HTTP POST
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

System diagnostics
------------------

WebMon displays system diagnostics information on https://monitor.sns.gov/dasmon/common/diagnostics/
and diagnostics for DASMON and PVSD at the beamline at
`https://monitor.sns.gov/dasmon/<instrument>/diagnostics/
<https://monitor.sns.gov/dasmon/cg3/diagnostics/>`_.
Diagnostics information is primarily collected by Dasmon listener.

Heartbeats from services
........................

Dasmon listener subscribes to heartbeats from the other services. There is a mechanism for alerting
admins by email when a service has missed heartbeats (needs to be verified that this still works).

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
