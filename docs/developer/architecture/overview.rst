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

Inter-service communication
---------------------------

WebMon uses an `ActiveMQ <https://activemq.apache.org/>`_ message broker as the main method of
communication between services. The message broker also serves as a load balancer by distributing
post-processing jobs to the available autoreducers in a round-robin fashion. Communication with Live
Data Server and ONCat occurs via their respective REST API:s.

Table 1 lists the type of communication between pairs services, which are loosely categorized as
"client" and "service" in that interaction.

.. list-table:: Table 1: Inter-service communication types
   :widths: 25 25 50
   :header-rows: 1

   * - "Client"
     - "Server"
     - Communication type
   * - Autoreducers
     - Dasmon Listener
     - Message queue
   * - Autoreducers
     - Live Data Server
     - REST API
   * - Autoreducers
     - ONCat
     - REST API
   * - DASMON
     - Dasmon Listener
     - Message queue
   * - DASMON
     - Workflow DB
     - Direct database
   * - Dasmon Listener
     - Workflow DB
     - Direct database
   * - Live Data Server
     - Live Data DB
     - Direct database
   * - Livereduce
     - Live Data Server
     - REST API
   * - Livereduce
     - Stream Management Service
     - Stream socket
   * - Process Variable Streaming Daemon (PVSD)
     - Dasmon Listener
     - Message queue
   * - Stream Management Service (SMS)
     - Dasmon Listener
     - Message queue
   * - Streaming Translation Client (STC)
     - Dasmon Listener
     - Message queue
   * - Streaming Translation Client (STC)
     - Workflow Manager
     - Message queue
   * - Workflow Manager
     - Autoreducers
     - Message queue
   * - Workflow Manager
     - Dasmon Listener
     - Message queue
   * - Workflow Manager
     - Workflow DB
     - Direct database
   * - WebMon frontend
     - Live Data Server
     - REST API
   * - WebMon frontend
     - ONCat
     - REST API
   * - WebMon frontend
     - Workflow DB
     - Direct database
