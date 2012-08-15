data_workflow
=============

WARNING: This software is still a feasibility prototype.

SNS data workflow manager and reporting app

	Dependencies: stomp (http://code.google.com/p/stomppy/)
	              django (https://www.djangoproject.com/)
	              MySQLdb (https://sourceforge.net/projects/mysql-python/)

- Workflow: Data workflow manager based on ActiveMQ.

	The database abstraction is done through django.db and the
	communication layer is done using stomp.py
	
	The icat_activemq.xml file is the ActiveMQ configuration used to set up the 
	cluster of brokers.
	
	Use sns_post_processing.py to start the workflow manager.
	
	Use test/test_consumer.py to simulate the worker nodes.

- Reporting: Reporting application for the workflow manager.
	The reporting app is built using django. It connects to the reporting
	database used by the workflow manager.
