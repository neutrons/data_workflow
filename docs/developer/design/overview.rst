Design Overview
===============

.. toctree::
   :maxdepth: 1

   communication_flows


High-level architecture
-----------------------

The diagram below describes the high-level architecture of WebMon. The gray box labeled "DAS" are
services owned by the Data Acquisition System team that feed information to WebMon but are not part
of WebMon. The services communicate mainly through an ActiveMQ message broker. The communication
flow is described in :ref:`communication_flows`.

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
            PVSD
        end
        subgraph "Workflow Manager"
            WorkflowManager[Workflow Manager]
            DasmonListener[Dasmon listener]
            Database[(DB)]
        end
        subgraph Autoreduction
            Autoreducers-->|cataloging|ONCat
            LiveDataServer<-->LiveDataDB[(DB)]
            LiveReduce
        end
        subgraph Frontend
            WebMon["`WebMon
            monitor.sns.gov`"]
        end
        SMS-->|live data stream|LiveReduce
        TranslationService-->|trigger reduction|WorkflowManager
        DASMON-->|status|DasmonListener
        DASMON-->|PV updates|Database
        WorkflowManager<-->|instructions|Autoreducers
        Autoreducers-->|publish plots|LiveDataServer
        Database-->WebMon
        ONCat-->|run metadata|WebMon
        LiveDataServer-->|plots|WebMon
        LiveReduce-->|publish plots|LiveDataServer
        DasmonListener-->Database
        WorkflowManager-->Database
        TranslationService-->|NeXus file|FileArchive
        FileArchive<-->Autoreducers
        style DAS fill:#D3D3D3, stroke-dasharray: 5 5


High-level architecture
-----------------------

The diagram below describes the high-level architecture of WebMon. The gray box labeled "DAS" are
services owned by the Data Acquisition System team that feed information to WebMon, e.g. to trigger
autoreduction when a run is finished. The services mainly communicate through an ActiveMQ message
broker. The communication flow is described in :ref:`communication_flows`.

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
            PVSD
        end
        subgraph "Workflow Manager"
            WorkflowManager[Workflow Manager]
            DasmonListener[Dasmon listener]
            Database[(DB)]
        end
        subgraph Autoreduction
            Autoreducers-->|REST API|ONCat
            LiveDataServer<-->LiveDataDB[(DB)]
            LiveReduce
        end
        subgraph Frontend
            WebMon["`WebMon
            monitor.sns.gov`"]
        end
        SMS-->LiveReduce
        TranslationService-.->|ActiveMQ|WorkflowManager
        DASMON-.->|ActiveMQ|DasmonListener
        DASMON-->Database
        WorkflowManager<-.->|ActiveMQ|Autoreducers
        Autoreducers-->|REST API|LiveDataServer
        Database-->WebMon
        ONCat-->|REST API|WebMon
        LiveDataServer-->|REST API|WebMon
        LiveReduce-->|REST API|LiveDataServer
        DasmonListener-->Database
        WorkflowManager-->Database
        TranslationService-->FileArchive
        FileArchive<-->Autoreducers
        style DAS fill:#D3D3D3, stroke-dasharray: 5 5
