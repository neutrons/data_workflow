Data Workflow Manager
---------------------

SNS data workflow manager and reporting app

	Dependencies: stomp (http://code.google.com/p/stomppy/)
	              django (https://www.djangoproject.com/)
	              MySQLdb (https://sourceforge.net/projects/mysql-python/) if using MySQL
	              psycopg2 (http://initd.org/psycopg/) if using PostgreSQL

- Workflow: Data workflow manager based on ActiveMQ.

	The database abstraction is done through django.db and the
	communication layer is done using stomp.py
	
	The `icat_activemq.xml` file is the ActiveMQ configuration used to set up the 
	cluster of brokers.
	
	Use `sns_post_processing.py` to start the workflow manager.
	
	Use `test/test_consumer.py` to simulate the worker nodes.

- Reporting: Reporting application for the workflow manager.
	The reporting app is built using django. It connects to the reporting
	database used by the workflow manager.

	Apache installation:
	- Make sure djando, stomp and psycopq2 (or MySQLdb if using MySQL) are properly installed
	- Make sure the DB information in `/var/www/workflow/app/reporting_app/settings.py` is correct
	- Run make install, which will install the app in `/var/www/workflow`
	- If you don't have `mod_wsgi` on your system, get it here: http://code.google.com/p/modwsgi
	- Add the following lines to `httpd.conf`
		LoadModule `wsgi_module libexec/apache2/mod_wsgi.so`
		Include `/var/www/workflow/apache/apache_django_wsgi.conf`
	- `apachectl restart`	
	
	Note: if you get an error to the effect that _mysql.so is unable to find libmysqlclient.18.dylib,
	make sure you have a sym link in /usr/lib pointing to /usr/local/mysql/lib
	(http://stackoverflow.com/questions/6383310/python-mysqldb-library-not-loaded-libmysqlclient-18-dylib)
	
- PostgreSQL optimization:
	If using PostgreSQL, you can install the stored procedure in `reporting/report/sql/stored_procs.sql`.
	Those will speed up the run rate and error rate queries. No change needs to be made
	to the settings when installing those stored procedures and the application will
	use them automatically.