Release notes
=============

v3.0.0rc2
------

The development team is very happy to announce this release which focused on modernization and security fixes, as well as the dockerization, environment setup, and documentation.

The main purpose of this release is to address security issues with how user's work is run on remote worker nodes.
The new method of security creates a ssh key pair that is unique to the session and deleted when either the user logs out or abandons the session (idle for 24 hours).
The other feature of the ssh key is that it is only accepted for connections from the host that created it.

Dependency changes

- python 2.7 to 3.7
- apache to nginx
- django 1.11 to 3.2
- jquery 1.72 to 3.6
- sqlite to postgress

Other modernization changes include a heavily increased test coverage (currently 77%), building python wheels, and a `sphinx site <https://data-workflow.readthedocs.io/en/latest/>`_ .

In addition to the various other changes since the last release of 2.8.0 in 2015.
