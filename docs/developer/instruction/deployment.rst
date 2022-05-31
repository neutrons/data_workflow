Deployment
==========

Deployments:

* TEST deployment http://webmon-test.ornl.gov
* PROD deployment https://monitor.sns.gov


Continuous Integration artifacts
--------------------------------

We are deploying the following docker images:

* `webmon <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Fwebmon>`_
* `dasmon <https://github.com/orgs/neutrons/packages/container/package/data_workflow%2Fdasmon>`_
* `workflow <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Fworkflow>`_
* `autoreducer <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Fautoreducer>`_
* `pv_test_gen <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Fpv_test_gen>`_
* `amp_test_gen <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Famq_test_gen>`_
* `catalog <https://github.com/neutrons/data_workflow/pkgs/container/data_workflow%2Fcatalog>`_

Infrastructure
--------------

Infrastructure repository that creates infrastructure for this deployment: https://code.ornl.gov/sns-hfir-scse/infrastructure/neutrons-test-environment

Deployment repositories Dockerfiles
-----------------------------------

The deployment is done with docker-compose within GitLab jobs. All
services are deployed for the TEST deployment while for the PROD
deployment only **web-monitor**, **workflow-db** and **workflow-mgr**
are deployment with this system. All the deployment repos can be found
at https://code.ornl.gov/sns-hfir-scse/deployments.

The **web-monitor-deploy** CI will trigger the deployment of all the
other repositories except the database and ActiveMQ.

The docker-compose files for TEST and PROD are the following:

============ ========================== ====================================================================================================================================== ====
Service      repo                       TEST                                                                                                                                   PROD
============ ========================== ====================================================================================================================================== ====
web-monitor  web-monitor-deploy         `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/web-monitor-deploy/-/blob/main/test/docker-compose.yml>`_         *TODO*
workflow-db  workflow-db-deploy         `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/workflow-db-deploy/-/blob/main/test/docker-compose.yml>`_         *TODO*
amqbroker    amqbroker-deploy           `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/amqbroker-deploy/-/blob/main/test/docker-compose.yml>`_           *N/A*
workflow-mgr workflow-mgr-deploy        `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/workflow-mgr-deploy/-/blob/main/test/docker-compose.yml>`_        *TODO*
autoreducer  autoreducer-deploy         `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/autoreducer-deploy/-/blob/main/test/docker-compose.yml>`_         *N/A*
catalog      catalog-emulator-deploy    `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/catalog-emulator-deploy/-/blob/main/test/docker-compose.yml>`_    *N/A*
testfixtures webmon-testfixtures-deploy `docker-compose.yml <https://code.ornl.gov/sns-hfir-scse/deployments/webmon-testfixtures-deploy/-/blob/main/test/docker-compose.yml>`_ *N/A*
============ ========================== ====================================================================================================================================== ====

Configuration
-------------

All environment variable are set in the docker-compose files except
those that are marked secret which are set in the GitLab CI variables.

web-monitor environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
AMQ_BROKER                    List of ActiveMQ brokers
APP_SECRET             yes    `Django SECRET_KEY <https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key>`_
CATALOG_ID             yes    `ONCat client ID <https://oncat.ornl.gov/#/build?section=authentication>`_
CATALOG_SECRET         yes    `ONCat client secret <https://oncat.ornl.gov/#/build?section=authentication>`_
CATALOG_URL            yes    `ONCat URL <https://oncat.ornl.gov>`_
DATABASE_HOST                 PostgreSQL hostname
DATABASE_NAME                 Database name
DATABASE_PASS          yes    PostgreSQL Owner password|
DATABASE_PORT                 PostgreSQL post
DATABASE_USER                 PostgreSQL Owner username
DJANGO_SETTINGS_MODULE        `Description of settings <https://data-workflow.readthedocs.io/en/latest/developer/instruction/build.html?highlight=DJANGO_SETTINGS_MODULE#description-of-settings>`_
ICAT_PASS              yes    ActiveMQ password
ICAT_USER                     ActiveMQ username
LDAP_CERT_FILE         yes    `ldap.OPT_X_TLS_CACERTFILE <https://www.python-ldap.org/en/latest/reference/ldap.html#ldap.OPT_X_TLS_CACERTFILE>`_
LDAP_DOMAIN_COMPONENT  yes    Use in `AUTH_LDAP_USER_DN_TEMPLATE <https://django-auth-ldap.readthedocs.io/en/latest/reference.html#std:setting-AUTH_LDAP_USER_DN_TEMPLATE>`_
LDAP_SERVER_URI        yes    `AUTH_LDAP_SERVER_URI <https://django-auth-ldap.readthedocs.io/en/latest/reference.html#auth-ldap-server-uri>`_
TIME_ZONE                     `Time zone to use <https://docs.djangoproject.com/en/3.2/ref/settings/#time-zone-1>`_
====================== ====== ===========

workflow-db environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
POSTGRES_DB                   Database name
POSTGRES_PASSWORD      yes    PostgreSQL Owner password
POSTGRES_USER                 PostgreSQL Owner username
====================== ====== ===========

workflow-mgr environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
AMQ_BROKER                    List of ActiveMQ brokers
AMQ_QUEUE                     List of ActiveMQ queues dasmon should listen to|
APP_SECRET             yes    `Django SECRET_KEY <https://docs.djangoproject.com/en/3.2/ref/settings/#secret-key>`_
DATABASE_HOST                 PostgreSQL hostname
DATABASE_NAME                 Database name
DATABASE_PASS          yes    PostgreSQL Owner password|
DATABASE_PORT                 PostgreSQL post
DATABASE_USER                 PostgreSQL Owner username
ICAT_PASS              yes    ActiveMQ password
ICAT_USER                     ActiveMQ username
TIME_ZONE                     `Time zone to use <https://docs.djangoproject.com/en/3.2/ref/settings/#time-zone-1>`_
WORKFLOW_USER                 ActiveMQ workflow username
WORKFLOW_PASS          yes    ActiveMQ workflow password
====================== ====== ===========

catalog environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
ACTIVE_MQ_HOST                ActiveMQ hostname
ACTIVE_MQ_PORTS               ActiveMQ port
ICAT_PASS              yes    ActiveMQ password
ICAT_USER                     ActiveMQ username
====================== ====== ===========

testfixtures environment variables
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
BROKER                        ActiveMQ broker address
DATABASE_HOST                 PostgreSQL hostname
DATABASE_NAME                 Database name
DATABASE_PASS          yes    PostgreSQL Owner password|
DATABASE_PORT                 PostgreSQL post
DATABASE_USER                 PostgreSQL Owner username
ICAT_PASS              yes    ActiveMQ password
ICAT_USER                     ActiveMQ username
====================== ====== ===========

Additional configuration files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* **amqbroker-deploy** -> `icat_activemq.xml <https://code.ornl.gov/sns-hfir-scse/deployments/amqbroker-deploy/-/blob/main/test/icat_activemq.xml>`_

  * icat and workflow username and passwords are set in here

* **autoreducer-deploy** -> `post_processing.conf <https://code.ornl.gov/sns-hfir-scse/deployments/autoreducer-deploy/-/blob/main/test/post_processing.conf>`_

  * ActiveMQ server address needs to be set in here
  * icat username and password needs to be set in here

* **web-monitor-deploy** -> `nginx <https://code.ornl.gov/sns-hfir-scse/deployments/web-monitor-deploy/-/tree/main/test/nginx>`_

Notes
^^^^^

You need to make sure the following variables match:

* ``DATABASE_*`` in **web-monitor**, **workflow-mgr** and **testfixtures**, and **POSTGRES_*** in database
* ``ICAT_USER`` and ``ICAT_PASS`` in **web-monitor**, **workflow-mgr**, **catalog** and **testfixtures**, and **amqbroker** (``icat_activemq.xml``) and **autoreducer** (``post_processing.conf``)
* ``WORKFLOW_USER`` and ``WORKFLOW_PASS`` in **workflow-mgr** and in **amqbroker** (``icat_activemq.xml``)
