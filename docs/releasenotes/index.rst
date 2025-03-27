Release notes
=============

v3.3.0
------

We are excited to announce the **v3.3.0** release, which brings a few notable changes:

- **Legacy Dashboard Removed**: The old *Dashboard* interface has been removed. All monitoring
  and post-processing features are now accessed through the main Web Monitor interface.
- **REF_M Vertical Mode**: For the Magnetism Reflectometer (REF_M) instrument, a *Vertical* geometry
  mode is now supported in the auto-reduction setup. Runs collected in this mode are cataloged
  and processed just like any other runs.
- **New Management Command**: A new `add_indices` command was introduced to create additional
  database indexes, improving performance for reporting queries. Be sure to run it after
  updating to v3.3.0.
- **Updated Run Status**: Runs currently being acquired are labeled *“Acquiring”* (instead of the
  older “Running”). This clarifies the data-collection state at a glance.
- **Various Internal Improvements**: This release includes several performance enhancements
  and dependency bumps. Notably, the JavaScript build tool was upgraded (Grunt 1.4.1 → 1.5.3),
  and caching mechanisms were optimized to reduce load on the database.

Please refer to the documentation for further details on these changes and to ensure
your environment is updated correctly.

v3.0.0
------

The development team is very happy to announce this release which focused on modernization, dockerization, environment setup, and documentation.

Dependency changes

- python 2.7 to 3.10
- apache to nginx
- django 1.11 to 3.2
- jquery 1.72 to 3.6
- postgess 9.6.23 to 14

Other modernization changes include a heavily increased test coverage (currently 77%), building python wheels, and a `sphinx site <https://data-workflow.readthedocs.io/en/latest/>`_ .

In addition to the various other changes since the last release of 2.8.0 in 2015.
