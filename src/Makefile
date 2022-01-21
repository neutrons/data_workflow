prefix := /var/www/workflow
DJANGO_COMPATIBLE:=$(shell python3 -c "import django;t=0 if django.VERSION[1]<6 else 1; print(t)")

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
	@python3 -c "import django" || echo "\nERROR: Django is not installed: www.djangoproject.com\n"
	@python3 -c "import psycopg2" || echo "\nWARNING: psycopg2 is not installed: http://initd.org/psycopg\n"
	@python3 -c "import stomp" || echo "\nERROR: stomp.py is not installed: http://code.google.com/p/stomppy\n"
	#@python3 -c "import pyoncat" || pip install https://oncat.ornl.gov/packages/PyONCat-1.0rc4-py2.py3-none-any.whl

workflow: check
	# Install the workflow manager, which defines the database schema
	python3 setup.py install

clean:
	test -f setup.py && python3 setup.py clean
	test -f setup_dasmon_listener.py && python3 setup_dasmon_listener.py clean
	rm -fR *.pyc
	rm -fR build/

dasmonlistener: workflow
	# Install DASMON listener
	python3 setup_dasmon_listener.py clean
	python3 setup_dasmon_listener.py install

webmon/core: workflow  # the dependency on workflow doesn't make sense
	# Make sure the install directories exist
	# this will create parent directories
	mkdir -m 0755 -p $(prefix)/app
	mkdir -m 0755 -p $(prefix)/static/web_monitor

webmon: webmon/core
	# Install application code from reporting
	cp reporting/manage.py $(prefix)/app
	cp -R reporting/report $(prefix)/app
	cp -R reporting/dasmon $(prefix)/app
	cp -R reporting/reduction $(prefix)/app
	cp -R reporting/pvmon $(prefix)/app
	cp -R reporting/static $(prefix)/app
	cp -R reporting/users $(prefix)/app
	cp -R reporting/templates $(prefix)/app
	cp -R reporting/reporting_app $(prefix)/app

	# Install apache config
	cp -R reporting/apache $(prefix)

	# Collect the static files and install them
	cd $(prefix)/app; python3 manage.py collectstatic --noinput

	# Create the database tables. The database itself must have been
	# created on the server already

	cd $(prefix)/app; python3 manage.py makemigrations --noinput
	cd $(prefix)/app; python3 manage.py migrate --noinput
	cd $(prefix)/app; python3 manage.py migrate --run-syncdb --noinput

	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	cd $(prefix)/app; python3 manage.py createcachetable webcache
	cd $(prefix)/app; python3 manage.py ensure_adminuser --username=${DATABASE_USER} --email='workflow@example.com' --password=${DATABASE_PASS}

	# Modify and copy the wsgi configuration
	#cp reporting/apache/apache_django_wsgi.conf /etc/httpd/conf.d

	# pass the init sql script to dbshell
	cd $(prefix)/app; python3 manage.py dbshell < report/sql/indices.sql
	cd $(prefix)/app; python3 manage.py dbshell < report/sql/statusqueue.sql
	cd $(prefix)/app; python3 manage.py dbshell < report/sql/stored_procs.sql

	@echo "\n\nReady to go: run apachectl restart\n"

.PHONY: check
.PHONY: workflow
.PHONY: webmon
.PHONY: webmon/core
.PHONY: dasmonlistener
.PHONY: test
