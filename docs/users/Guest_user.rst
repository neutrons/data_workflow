Guest User View
===============

.. toctree::
   :maxdepth: 2

Anyone can see a list of instruments

.. image:: images/example_guest_user.png
   :width: 100%
   :align: center
   :alt: guest user view example

When clicking on any instrument one can see the status of the instrument

.. image:: images/example_instrument_status_guest_user.png
   :width: 100%
   :align: center
   :alt: guest user view of instrument status example

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

Note that guest users don't have access to the data, so clicking on any run will prompt the user to log in with
their `UCAMS/XCAMS <https://user.ornl.gov/Account/Login>`_ credentials

.. image:: images/example_data_access_denied.png
   :width: 100%
   :align: center
   :alt: example view of data access denied viewed as guest user
