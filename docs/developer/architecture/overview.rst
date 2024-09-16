Overview
========

High-level architecture
-----------------------

The diagram below describes the high-level architecture of WebMon, including both internal resources
that are considered part of WebMon and external systems that WebMon interacts with.
The arrows represent relationships between these services and resources.

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
        classDef externalStyle fill:#FAEFDE, stroke:#B08D55
        class DASMON,TranslationService,SMS,FileArchive,ONCat externalStyle

        subgraph Legend
            direction LR
            Internal["Internal resource"]
            External["External resource"]
            Internal ~~~ External
        end
        LiveReduce ~~~ Internal
        style Legend fill:#FFFFFF,stroke:#000000
        class External externalStyle

The gray box labeled "DAS" are services managed by the Data Acquisition System team that pass
information to WebMon. The autoreducers interact with the HFIR/SNS file archive to access
instrument-specific reduction scripts and experiment data files. The autoreducers also write reduced
data files and reduction log files back to the file archive.

Another external component is the experiment data catalog, `ONCat <https://oncat.ornl.gov/>`_, where
the autoreducers catalog experiment metadata. The WebMon frontend retrieves and displays this
metadata from ONCat.

The section :ref:`communication_flows` includes sequence diagrams that show how the services
interact.

Message broker
--------------

WebMon uses an `ActiveMQ <https://activemq.apache.org/>`_ message broker for communication between
services. The message broker also serves as a load balancer by distributing post-processing jobs to
the available autoreducers in a round-robin fashion.

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
