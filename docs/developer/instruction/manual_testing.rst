Manual testing
==============

Guest View
----------

Web Monitor should be tested for the :doc:`Guest User View
<../../users/usecases/Guest_user>` use case.

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
