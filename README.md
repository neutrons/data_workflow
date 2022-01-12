
[![CI](https://github.com/neutrons/data_workflow/actions/workflows/ci.yml/badge.svg?branch=next)](https://github.com/neutrons/data_workflow/actions/workflows/ci.yml?query=branch:next)
[![codecov](https://codecov.io/gh/neutrons/data_workflow/branch/next/graph/badge.svg?token=q1f07RUI88)](https://codecov.io/gh/neutrons/data_workflow)
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/5504/badge)](https://bestpractices.coreinfrastructure.org/projects/5504)

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

- Web monitor: Reporting application for the workflow manager.
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

- DASMON listener: DB logging daemon.
    The DASMON listener watches for DASMON message sent to ActiveMQ and logs them.
	See the `dasmon_listener/README.md` file for more details.

- PostgreSQL optimization:
	If using PostgreSQL, you can install the stored procedure in `reporting/report/sql/stored_procs.sql`.
	Those will speed up the run rate and error rate queries. No change needs to be made
	to the settings when installing those stored procedures and the application will
	use them automatically.

[![DOI Badge](https://zenodo.org/badge/4139/neutrons/data_workflow.png)](http://dx.doi.org/10.5281/zenodo.10054)

## Setup Dev Environment with docker-compose

During the modernization of WebMon, the developers can setup a local development environment using docker compose.
Here are the recommended steps to setup your dev environment:

- Clone the repository as usual.
- Install `docker` and [`docker-compose`](https://docs.docker.com/compose/install/) if they are not present on your system.
- Cleanup containers, volumes and images from previous run (skip this step if this is the first time)
  - Use `docker container prune` to prune all stopped containers
  - Use `docker volume prune` to prune all volumes
  - [Optional] Use `docker image prune` to remove all images
- Move to the directory that contains `docker-compose.yml` (the root of repo)
- Spin up the rest of the system with (`--build` may be unnecessary)
  > docker-compose up --build
  - Keep this running in your terminal so that you can see the real time log from all containers
  - `--build` will ensure any local changes will be updated in containers at the cost of increasing the startup time
- Open a browser and go to `localhost:8000` to see the login page
- Log in with the newly added super user (defined through `DATABASE_USER` and `DATABASE_PASS` variables in `.env` file)
  - user name: `postgres`
  - password: `postgres`
- After editing the source code, you


## Running unit tests

- `conda env create --file conda_environment.yml` or `conda env update --file conda_environment.yml` if the environment already exists
- `conda activate webmon`
- `python -m pip install -r requirements_test.txt`
- `python -m pytest src`
