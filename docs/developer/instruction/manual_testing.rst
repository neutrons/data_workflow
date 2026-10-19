Manual testing
==============

Guest View
----------

Every page and data update requires logging in, wherever you connect
from. Being on the ORNL network no longer gives access without a login.

Without logging in, opening any page should redirect you to the login
page, and data update URLs such as ``/pvmon/<instrument>/update/``
should return 401. Check this both on and off the ORNL network.

General User View
-----------------

Web Monitor should be tested for the :doc:`General User View
<../../users/General_user>` use case.

To test these views from a general user's perspective you must login
with an account that has the appropriate permissions.  The account
must have access to a run populated with enough data to confirm
the elements in the above doc appear and are functional.

For instance, the example in the docs uses https://monitor.sns.gov/report/arcs/214581/
Please ensure you can access it or a run like it on monitor.sns.gov before
proceeding with the test.

Please confirm:
    * Catalog information appears at the top of the page
    * Then the plot data appears next and is interactable


Instrument Scientist View
-------------------------

Web Monitor should be tested for the :doc:`Instrument Scientist View
<../../users/Instrument_scientist>` use case.

Please confirm the UI elements that appeared in the General User View also
appear when logged in as an Instrument Scientist.

In addition, please ensure the post-processing buttons that appear in the first
screenshot are interactable and return no error when submitted.

Follow the directions in the linked Instrument Scientist View doc to open
the autoreduction page.  Fill in the information listed, including clicking
the small round plus icon to add additional mask info, and submit.
Ensure no error is returned or appears on the page.
Click the reset button, ensure this also does not result in an error.

Finally, follow the directions to open the postprocessing page.  Again,
fill in the form and hit submit.  Ensure no error is returned.  Then attempt
to find the job you just submitted by filling in the exact same information and
instead clicking the 'find' button.
