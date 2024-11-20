Release notes
=============

<Next Major or Minor Release>
-----------------------------
(date of release, format YYYY-MM-DD)



3.1.3
-----
2024-06-21

* Change default CATALOG_DATA_READY to OnCat by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/164
* Update Django model dasmon_statusvariable id field to bigint by @backmari in https://github.com/neutrons/data_workflow/pull/165

3.1.2
-----
2024-05-10

* Fix docs build and broken links, formatting by @backmari in https://github.com/neutrons/data_workflow/pull/149
* Documentation for making changes to the autoreduction configuration form by @backmari in https://github.com/neutrons/data_workflow/pull/151
* Add link for related projects by @peterfpeterson in https://github.com/neutrons/data_workflow/pull/152
* Update pyoncat source to conda by @KedoKudo in https://github.com/neutrons/data_workflow/pull/153
* Update Dockerfile.autoreducer to use latest RPM of post processing agent by @backmari in https://github.com/neutrons/data_workflow/pull/154
* Replace ActiveMQ docker image with security vulnerabilities by @backmari in https://github.com/neutrons/data_workflow/pull/155
* Fix error thrown when the task_class of a task is None by @backmari in https://github.com/neutrons/data_workflow/pull/156
* Versioningit next version by @backmari in https://github.com/neutrons/data_workflow/pull/157
* Add user documentation on troubleshooting by @backmari in https://github.com/neutrons/data_workflow/pull/158
* Move autoreducer to 3.1 in docker containers and add systemtest for new HIMEM autoreducer queue by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/159
* Make list of HFIR instruments complete by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/160
* Configurable Live Data Server domain name by @backmari in https://github.com/neutrons/data_workflow/pull/162
* Update to post-processing agent 3.2.0 by @backmari in https://github.com/neutrons/data_workflow/pull/163

3.1.1
-----
2023-05-08

* Set MonitoredVariable table values by @searscr in https://github.com/neutrons/data_workflow/pull/148

v3.0.2
------
2023-02-09

* Remove quotes from env var by @jmborr in https://github.com/neutrons/data_workflow/pull/140
* Fix Data download link by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/141
* Change datetime format to something parsable by python datetime by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/143
* Add admin documentation by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/144
* Add information about additional parameters by @peterfpeterson in https://github.com/neutrons/data_workflow/pull/145

v3.0.1
------
2022-08-29

* Add DASMON/PVSD system status badges to instruments by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/133
* Add a link to extended dashboard from latest run page by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/134
* Trim resolution in time to miliseconds by @peterfpeterson in https://github.com/neutrons/data_workflow/pull/131
* Clearer logs for error messages by @peterfpeterson in https://github.com/neutrons/data_workflow/pull/132
* Tighten dashboard layouts by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/135
* Loading a Database Dump in LOCAL environment by @jmborr in https://github.com/neutrons/data_workflow/pull/136
* Customize 'Add monitored variable' form instead of using a custom action by @rosswhitfield in https://github.com/neutrons/data_workflow/pull/137
* Pull fit link out of html_data condition by @jmborr in https://github.com/neutrons/data_workflow/pull/138

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
