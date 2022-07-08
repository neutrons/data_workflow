Deployment
==========

To deploy the web-monitor, you require **web-monitor**,
**workflow-db** and **workflow-mgr**. For test deployments there are
also **catalog**, **testfixtures**, **amqbroker** and **autoreducer**
to fake external services.

Configuration
-------------

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
DATABASE_PASS          yes    PostgreSQL Owner password
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

catalog environment variables (TEST only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====================== ====== ===========
Variable               Secret Description
====================== ====== ===========
ACTIVE_MQ_HOST                ActiveMQ hostname
ACTIVE_MQ_PORTS               ActiveMQ port
ICAT_PASS              yes    ActiveMQ password
ICAT_USER                     ActiveMQ username
====================== ====== ===========

testfixtures environment variables (TEST only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

* **amqbroker-deploy** (TEST only) -> `icat_activemq.xml <https://github.com/neutrons/data_workflow/blob/next/src/workflow_app/workflow/icat_activemq.xml>`_

  * icat and workflow username and passwords are set in here

* **autoreducer-deploy** (TEST only)-> `post_processing.conf <https://github.com/neutrons/post_processing_agent/tree/main/configuration>`_

  * ActiveMQ server address needs to be set in here
  * icat username and password needs to be set in here

* **web-monitor-deploy** -> `nginx conf <https://github.com/neutrons/data_workflow/blob/next/nginx/django.conf>`_

Notes
^^^^^

You need to make sure the following variables match:

* ``DATABASE_*`` in **web-monitor**, **workflow-mgr** and **testfixtures**, and **POSTGRES_*** in database
* ``ICAT_USER`` and ``ICAT_PASS`` in **web-monitor**, **workflow-mgr**, **catalog** and **testfixtures**, and **amqbroker** (``icat_activemq.xml``) and **autoreducer** (``post_processing.conf``)
* ``WORKFLOW_USER`` and ``WORKFLOW_PASS`` in **workflow-mgr** and in **amqbroker** (``icat_activemq.xml``)
