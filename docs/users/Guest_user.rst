Guest User View
===============

.. toctree::
   :maxdepth: 2

Anyone can see a list of instruments and whether each one is running.

.. image:: images/example_guest_user.png
   :width: 100%
   :align: center
   :alt: guest user view example

Everything else requires logging in with your `UCAMS/XCAMS <https://user.ornl.gov/Account/Login>`_
credentials. Clicking on an instrument takes you to the login page, and the pages below are what you'll
see once you're logged in.

When clicking on any instrument one can see the status of the instrument. The status page shows a
list of *monitored variables*. The sample logs to display can be configured in CSS (the frontend
interface for the instrument control), see instructions
`here <https://powder.ornl.gov/general_aspects/data_acquire/monitor.html>`_.

.. image:: images/example_instrument_status_guest_user.png
   :width: 100%
   :align: center
   :alt: guest user view of instrument status example
|

In the top right hand side, there are links to see the runs in the current
experiment, together with the processing status.

.. image:: images/example_run_list.png
   :width: 100%
   :align: center
   :alt: example view of run list viewed as guest user

For example, runs that are actively collecting data will display a status of
*“Acquiring”*. Once acquisition finishes, the run may move to a *“Processing”*
status, and finally show *“Complete”* once processing is done.

In addition, there is a list of process variables (PVs). These are a list of sample
environment and instrument parameter logs.
If one clicks on a PV link, it will show the history of that PV in the last 15 minutes or 2 hours.
The ``y`` scale can be switched between linear and logarithmic.

.. image:: images/example_pv_list.png
   :width: 100%
   :align: center
   :alt: example view of PV list viewed as guest user


Clicking on the instrument name in the breadcrumbs will display a list of `IPTS <https://ipts.ornl.gov>`_ experiments

.. image:: images/example_IPTS_list.png
   :width: 100%
   :align: center
   :alt: example view of IPTS list viewed as guest user

Run details are only shown to members of the experiment or the instrument team. Anyone else who clicks on a
run will see that they don't have access to the data

.. image:: images/example_data_access_denied.png
   :width: 100%
   :align: center
   :alt: example view of data access denied viewed as guest user
