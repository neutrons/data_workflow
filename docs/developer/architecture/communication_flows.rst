.. _communication_flows:

.. Note that the mermaid diagrams are styled using some ugly CSS since styling of sequence diagrams
   is an open issue: https://github.com/mermaid-js/mermaid/issues/523
   CSS hack from: https://stackoverflow.com/questions/63587556/color-change-of-one-element-in-a-mermaid-sequence-diagram

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
        %%{init:{'themeCSS':'g:nth-of-type(6) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(2) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };'}}%%

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
        %%{init:{'themeCSS':'g:nth-of-type(2) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(5) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };'}}%%


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
        participant Post-Processing Agent
        participant ONCat
        participant HFIR/SNS File Archive

        STC->>Workflow Manager: POSTPROCESS.DATA_READY
        Workflow Manager->>Post-Processing Agent: CATALOG.ONCAT.DATA_READY
        Post-Processing Agent->>Workflow Manager: CATALOG.ONCAT.STARTED
        Post-Processing Agent->>ONCat: pyoncat
        Post-Processing Agent->>Workflow Manager: CATALOG.ONCAT.COMPLETE
        Workflow Manager->>Post-Processing Agent: REDUCTION.DATA_READY
        Post-Processing Agent->>Workflow Manager: REDUCTION.STARTED
        Post-Processing Agent->>HFIR/SNS File Archive: reduced data, reduction log
        Post-Processing Agent->>Workflow Manager: REDUCTION.COMPLETE
        Workflow Manager->>Post-Processing Agent: REDUCTION_CATALOG.DATA_READY
        Post-Processing Agent->>Workflow Manager: REDUCTION_CATALOG.STARTED
        Post-Processing Agent->>ONCat: pyoncat
        Post-Processing Agent->>Workflow Manager: REDUCTION_CATALOG.COMPLETE
        %%{init:{'themeCSS':'g:nth-of-type(2) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(5) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(6) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(7) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(10) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(11) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };'}}%%

Configuring the autoreduction
.............................

In addition to run post-processing, Post-Processing Agent handles updating instrument reduction
script parameters for instruments that have implemented
:doc:`autoreduction parameter configuration<../instruction/autoreduction>` at
`monitor.sns.gov/reduction/<instrument>/ <https://monitor.sns.gov/reduction/cncs/>`_.

.. mermaid::

    sequenceDiagram
        actor Instrument Scientist
        participant WebMon
        participant Post-Processing Agent
        participant HFIR/SNS File archive

        Instrument Scientist->>WebMon: Submit form with parameter values
        WebMon->>Post-Processing Agent: REDUCTION.CREATE_SCRIPT
        Post-Processing Agent->>HFIR/SNS File archive: Update instrument reduction script
        %%{init:{'themeCSS':'g:nth-of-type(5) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(9) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };'}}%%

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
        %%{init:{'themeCSS':'g:nth-of-type(2) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };g:nth-of-type(6) rect.actor { fill:#faf2e6; stroke:#f2e3cb; };'}}%%

Publish to Live Data Server from autoreduction script
.....................................................

The instrument-specific autoreduction script can include a step to publish plots (in either JSON
format or HTML div) to Live Data Server. The Post-Processing Agent repository includes some
convenience functions for generating and publishing plots in `publish_plot.py
<https://github.com/neutrons/post_processing_agent/blob/main/postprocessing/publish_plot.py>`_.

.. mermaid::

    sequenceDiagram
        participant Workflow Manager
        participant Post-Processing Agent
        participant Live Data Server

        Workflow Manager->>Post-Processing Agent: REDUCTION.DATA_READY
        opt Publish plot
            Post-Processing Agent->>Live Data Server: HTTP POST
        end

Display plot from Live Data Server
................................

Run overview pages (``monitor.sns.gov/report/<instrument>/<run number>/``) will query the Live
Data Server for a plot for that instrument and run number and display it, if available.

The Live Data Server database stores a single plot for each combination of instrument and run
number. Publishing a new plot automatically replaces the previous plot. When WebMon fetches a plot
it will, therefore, always display the latest plot, whether it was published by Livereduce during
the run or by autoreduction after the run has finished.

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

Dasmon listener subscribes to heartbeat messages from the other services and stores the last
received status for each service in the database. Post-Processing Agent and Workflow Manager
also include their process ID (PID) in the heartbeat message.

.. mermaid::

    flowchart LR
        SMS["SMS (per beamline)"]
        PVSD["PVSD (per beamline)"]
        DASMON["DASMON (per beamline)"]
        PostProcessingAgent["Post-Processing Agent"]
        DasmonListener
        WorkflowDB[(DB)]
        SMS-->|heartbeat|DasmonListener
        PVSD-->|heartbeat|DasmonListener
        DASMON-->|heartbeat|DasmonListener
        PostProcessingAgent-->|heartbeat, PID|DasmonListener
        WorkflowManager-->|heartbeat, PID|DasmonListener
        DasmonListener-->WorkflowDB
        classDef externalStyle fill:#faf2e6, stroke:#f2e3cb
        class SMS,PVSD,DASMON externalStyle

        subgraph Legend
            direction LR
            Internal["Internal resource"]
            External["External resource"]
            Internal ~~~ External
        end
        WorkflowManager ~~~ Internal
        style Legend fill:#FFFFFF,stroke:#000000
        class External externalStyle

Dasmon listener handles messages sent to a message broker topic with the string "STATUS" in the name
as heartbeat messages. For example, Workflow Manager sends a heartbeat message to
``SNS.COMMON.STATUS.WORKFLOW.0`` every 5 seconds. Dasmon listener also records heartbeats from the
beamline-specific services, e.g. the PVSD service at the HFIR beamline
CG3 sends heartbeat messages to the topic ``HFIR.CG3.STATUS.PVSD``. Table 2 lists the services that
send heartbeats to Dasmon listener, as well as their message broker topic and heartbeat frequency.

.. list-table:: Table 2: Service heartbeat messages
    :widths: 40 40 20
    :header-rows: 1

    * - Service
      - Message broker topic
      - Frequency
    * - Workflow Manager
      - SNS.COMMON.STATUS.WORKFLOW.0
      - 5 s
    * - Post-Processing Agent
      - SNS.COMMON.STATUS.AUTOREDUCE.0
      - 30 s
    * - DASMON
      - <facility>.<instrument>.STATUS.DASMON
      - 5 s
    * - PVSD
      - <facility>.<instrument>.STATUS.PVSD
      - 5 s
    * - SMS
      - <facility>.<instrument>.STATUS.SMS
      - 5 s
