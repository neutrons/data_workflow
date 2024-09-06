Design Overview
===============

.. toctree::
   :maxdepth: 1

   communication_flows


High-level architecture
-----------------------

The diagram below describes the high-level architecture of WebMon, including some external resources
that WebMon interacts with. The gray box labeled "DAS" are services owned by the Data Acquisition
System team that feed information to WebMon. `ONCat <https://oncat.ornl.gov/>`_ is the experiment
data catalog, which the autoreducers catalog runs to and the frontend fetches run metadata from.
The autoreducers access instrument-specific reduction scripts and experiment data files on the
HFIR/SNS file archive. The autoreducers also write reduced data files and logs to the file archive.

.. mermaid::

    flowchart LR
        FileArchive[("`SNS/HFIR
        File archive`")]
        subgraph DAS
            DASMON
            TranslationService["`Streaming
            Translation
            Client
            (STC)`"]
            SMS["`Stream
            Management
            Service
            (SMS)`"]
        end
        WorkflowManager[Workflow Manager]
        DasmonListener[Dasmon listener]
        Database[(Workflow DB)]
        Autoreducers-->ONCat
        LiveDataServer-->WebMon
        LiveDataServer<-->LiveDataDB[(LiveData DB)]
        LiveReduce
        WebMon["`WebMon
        frontend`"]
        SMS-->LiveReduce
        TranslationService-->WorkflowManager
        DASMON-->DasmonListener
        DASMON-->Database
        WorkflowManager-->Database
        WorkflowManager<-->Autoreducers
        Autoreducers-->LiveDataServer
        Database-->WebMon
        ONCat-->WebMon
        LiveReduce-->LiveDataServer
        DasmonListener-->Database
        TranslationService-->FileArchive
        FileArchive<-->Autoreducers
        style DAS fill:#D3D3D3, stroke-dasharray: 5 5
        classDef webMonStyle fill:#FFFFE0
        class WorkflowManager,DasmonListener,Database,Autoreducers,LiveDataServer,LiveReduce,WebMon,LiveDataDB webMonStyle

        subgraph Legend
            direction LR
            External["External resource"]
            Internal["Internal resource"]
            External ~~~ Internal
        end
        LiveReduce ~~~ External
        style Legend fill:#FFFFFF,stroke:#000000
        class Internal webMonStyle


Message broker
--------------

WebMon uses an `ActiveMQ <https://activemq.apache.org/>`_ message broker for communication between
services. The message broker also serves as a load balancer by distributing post-processing jobs to
the available autoreducers in a round-robin fashion.

Service communication flows are described in :ref:`communication_flows`.

.. mermaid::

    flowchart TB
        TranslationService["`Streaming
        Translation
        Client
        (STC)`"]
        SMS["`Stream
        Management
        Service
        (SMS)`"]
        Broker[ActiveMQ broker]
        Broker<-->Autoreducers
        Broker<-->WorkflowManager[Workflow Manager]
        Broker<-->DasmonListener[Dasmon listener]
        Broker<-->DASMON
        Broker<-->PVSD
        Broker<-->TranslationService
        Broker<-->SMS
