Glossary
========

.. glossary::
   :sorted:

   WebMon
      Monitor for instrument status and autoreduction status at SNS and HFIR. WebMon can refer to
      either the whole system or the landing page at https://monitor.sns.gov.

   DASMON
      Data Acquisition System Monitor (DASMON) is a per-beamline service that reports PV values and
      experiment/run meta-data to WebMon. Due to the high volume of PV updates, DASMON writes PV
      updates straight to the database. DASMON reports its status to WebMon for system diagnostics.

   DAS
      Data Acquisition System.

   SMS
      Stream Management Service (SMS) is a service that aggregates data from fast neutron event data
      and slow PVs into a data stream available for both live monitoring and file archiving. SMS
      reports its status to WebMon for system diagnostics.

   STC
      Streaming Translation Client (STC) is a service that translates the experiment data stream
      from :term:`SMS` to a NeXus data file. Triggers the post-processing workflow after the NeXus
      file has been created.

   PVSD
   Process Variable Streaming Daemon
      Per-beamline service that subscribes to EPICS Control System PV:s and forwards PV value
      changes to the SMS. PVSD reports its status to WebMon for system diagnostics.

   PV
      Process Variables (PVs) are variables coming from the control system and can include sample
      environment variables (e.g. temperature, magnetic field), instrument geometry and experiment
      metadata. Subsets of PVs are used for monitoring experiments.

   ONCat
      Catalog for neutron experiment data at SNS and HFIR: https://oncat.ornl.gov.

   SNS
      The Spallation Neutron Source at Oak Ridge National Laboratory.

   HFIR
      The High-Flux Isotope Reactor at Oak Ridge National Laboratory.

   NeXuS
      Data format for neutron, x-ray, and muon science.

   Workflow Manager
      Service that orchestrates the autoreduction/post-processing workflow.

   Dasmon listener
      Service that subscribes to messages from :term:`DASMON` and writes to the database.

   Autoreduction
      Automated data reduction that can be triggered when the run NeXuS data file is available. The
      instrument-specific autoreduction process is configured by the instrument scientist.
      Autoreduction is a step in the post-processing workflow.

   Cataloging
      Cataloging of experiment data in ONCat. Cataloging is a step in the post-processing workflow.

   Live Data Server
      Service that serves plots to the WebMon front-end. :term:`Livereduce` and
      :term:`autoreduction<Autoreduction>` can publish plots for a run to Live Data Server.

   Livereduce
      Service for live monitoring of the data stream for the creation of plots which are published
      to the :term:`Live Data Server`.

   IPTS
      Integrated Proposal Tracking System (IPTS) number is the experiment's proposal ID that is used
      for grouping runs.

   Workflow
      Experiment data post-processing workflow. The available tasks are cataloging, autoreduction
      and reduced data cataloging.

   Post-Processing Agent
      Service that performs post-processing tasks like cataloging and autoreduction.

   Autoreducer
      Server where an instance of :term:`Post-Processing Agent` is running.
