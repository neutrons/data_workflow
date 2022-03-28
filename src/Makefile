prefix := /var/www/workflow

# these are defined here becuase I couldn't figure out how to evaluate the commands
# during target execution rather then when make parses the file
# this is found by `find /opt/conda/ -name manage.py | grep reporting`
MANAGE_PY_WEBMON=/opt/conda/lib/python3.7/site-packages/reporting/manage.py
# this is found by `find /opt/conda -name db_init.json`
REPORT_DB_INIT=/opt/conda/lib/python3.7/site-packages/reporting/fixtures/db_init.json

all:

	@echo "Run make install to install the workflow manager and the web app"

check:
	########################################################################
	#                                                                      #
	# Make sure to check your DB settings in workflow/database/settings.py #
	# and reporting/reporting_app/settings.py                              #
	#                                                                      #
	########################################################################
	# Check dependencies
	which python
	echo CONDA_PREFIX=${CONDA_PREFIX}

	@python -c "import django" || echo "\nERROR: Django is not installed: www.djangoproject.com\n"
	@python -c "import psycopg2" || echo "\nWARNING: psycopg2 is not installed: http://initd.org/psycopg\n"
	@python -c "import stomp" || echo "\nERROR: stomp.py is not installed: http://code.google.com/p/stomppy\n"

wheel/dasmon:
	# make the wheel
	cd dasmon_app && python -m build --no-isolation --wheel
	# verify it is correct
	cd dasmon_app && check-wheel-contents dist/django_nscd_dasmon-*.whl

wheel/webmon:
	# make the wheel
	cd webmon_app && python -m build --no-isolation --wheel
	# verify it is correct - ignoring duplicate file check
	cd webmon_app && check-wheel-contents dist/django_nscd_webmon-*.whl

wheel/workflow:
	# make the wheel
	cd workflow_app && python -m build --no-isolation --wheel
	# verify it is correct
	cd workflow_app && check-wheel-contents dist/django_nscd_workflow-*.whl

install/workflow: check
	# Install the workflow manager, which defines the database schema
	pip install django_nscd_workflow*.whl
	# verify the install worked
	python -c "import workflow;print('WORKFLOW VERSION', workflow.__version__)"

install/dasmonlistener: install/workflow install/webmon
	# Install DASMON listener
	pip install django_nscd_dasmon*.whl
	# verify the install worked
	python -c "import dasmon_listener;print('DASMON VERSION', dasmon_listener.__version__)"

install/webmon: install/workflow
	# Install the main web application
	pip install django_nscd_webmon*.whl
	# verify the install worked
	python -c "import reporting;print('WEBMON VERSION', reporting.__version__)"

configure/webmon: install/webmon
	# Collect the static files and install them
	python $(MANAGE_PY_WEBMON) collectstatic --noinput

	# Create the database tables. The database itself must have been
	# created on the server already
	python $(MANAGE_PY_WEBMON) makemigrations --noinput
	python $(MANAGE_PY_WEBMON) migrate --noinput
	python $(MANAGE_PY_WEBMON) migrate --run-syncdb --noinput

	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	python $(MANAGE_PY_WEBMON) createcachetable webcache
	python $(MANAGE_PY_WEBMON) ensure_adminuser --username=${DATABASE_USER} --email='workflow@example.com' --password=${DATABASE_PASS}

	# Modify and copy the wsgi configuration
	#cp reporting/apache/apache_django_wsgi.conf /etc/httpd/conf.d

	# add the stored sql proceedures
	python $(MANAGE_PY_WEBMON) add_stored_procs

	# use fixtures to load initial data
	python $(MANAGE_PY_WEBMON) loaddata $(REPORT_DB_INIT)

	@echo "\n\nReady to go\n"

clean:
	cd dasmon_app && rm -rf build/ dist/
	cd webmon_app && rm -rf build/ dist/
	cd workflow_app && rm -rf build/ dist/

# targets that don't create actual files
.PHONY: check
.PHONY: configure/webmon
.PHONY: install/dasmonlistener
.PHONY: install/webmon
.PHONY: install/workflow
.PHONY: wheel/dasmon
.PHONY: wheel/webmon
.PHONY: wheel/workflow
