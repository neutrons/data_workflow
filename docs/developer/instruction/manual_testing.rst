Manual testing
==============

Guest View
----------

Web Monitor should be tested for the :doc:`Guest User View
<../../users/Guest_user>` use case.

The complications comes from that the behavior is dependent on the
domain you are accessing from.

The setting ``ALLOWED_DOMAIN`` defines which domains have access to
the Guest View, which allows you to see limited information without
logging in. The default domains are ``"ornl.gov"``, ``"sns.gov"``.

If connecting from the correct domain without logging in you should be
greeted with the list of instruments like is shown in the use case,
otherwise you will be redirected to login.

To test the behavior you can try any of the following
 * If connecting to ORNL with VPN, try with and without VPN to see the difference.
 * Change the ``ALLOWED_DOMAIN`` settings to a domain that matches you current domain and then to one that doesn't match
 * Connect from two different devices, one within the domain and one outside.

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
