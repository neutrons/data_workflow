How to Contribute
=================

.. toctree::
   :maxdepth: 2


Overview
--------

* Issue tracker: `https://github.com/neutrons/data_workflow/issues`_
* Documentation: `https://github.com/neutrons/data_workflow/tree/next/docs`_
* Source Code: `https://github.com/neutrons/data_workflow/src`_
* Tests: See `test_fixture`_ page for more details.


Contribute as a Developer of SCSE@ORNL
--------------------------------------

As a developer of the team SCSE@ORNL, you should request access to the internal issue tracking system for project `webmon`_.
When making a PR to introduce bug fixes or new features, please follow the guidelines below:

    * Use the ``next`` branch as the base.
    * Select the ``next`` branch as the target branch for your PR.
    * Add a link to the internal issue at the top of the PR description.
    * Provide a summary of the changes in the PR description.
    * Attach a screenshot of the affected page (if applicable).
    * Select a reviewer from the SCSE@ORNL team to review the PR.

Once the PR is approved and all tests pass, a senior developer will take care of the merging.
The feature will be available to the ``main`` branch at the start of the each release cycle.


Contributing as a User
----------------------

* Bug report and feature request:

   Please use the issue tracker to submit bug report and feature requests.

* Pull requests:

   Please fork the `webmon`_ project and submit a PR to the ``next`` branch.
   When submitting the PR, please make sure to include the following information in the description:

   * A link to the corresponding issue (if applicable).
   * A summary of changes introduced in the PR.
   * Attach a screenshot of the affected page (if applicable).
   * Select a reviewer from the SCSE@ORNL team to review the PR.

   Once the PR is approved and merged into ``next``, the feature will be available to the ``main`` branch at the start of the next release cycle.


.. _`https://github.com/neutrons/data_workflow/issues`: https://github.com/neutrons/data_workflow/issues
.. _`https://github.com/neutrons/data_workflow/tree/next/docs`: https://github.com/neutrons/data_workflow/tree/next/docs
.. _`https://github.com/neutrons/data_workflow/src`: https://github.com/neutrons/data_workflows/src
.. _`test_fixture`: test_fixture.html
.. _`webmon`: https://code.ornl.gov/sns-hfir-scse/infrastructure/web-monitor


.. only:: comment

   * The link to documentation should be updated to the corresponding read the doc page when it is available.
   * The unit tests are spread amount different Django applications, which is a compromise to follow the Django's convention.
