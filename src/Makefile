prefix := /var/www/workflow
HAS_MIGRATIONS:=$(shell python -c "import django;t=0 if django.VERSION[1]<7 else 1; print t")
DJANGO_COMPATIBLE:=$(shell python -c "import django;t=0 if django.VERSION[1]<6 else 1; print t")

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
	@python -c "import django" || echo "\nERROR: Django is not installed: www.djangoproject.com\n"
	@python -c "import psycopg2" || echo "\nWARNING: psycopg2 is not installed: http://initd.org/psycopg\n"
	@python -c "import stomp" || echo "\nERROR: stomp.py is not installed: http://code.google.com/p/stomppy\n"
	#@python -c "import pyoncat" || pip install https://oncat.ornl.gov/packages/PyONCat-1.0rc4-py2.py3-none-any.whl

ifeq ($(DJANGO_COMPATIBLE),1)
	@echo "Detected Django >= 1.6"
else
	$(error Detected Django < 1.6. The web monitor requires at least Django 1.6)
endif

workflow: check
	# Install the workflow manager, which defines the database schema
	python setup.py install

clean:
	python setup.py clean
	python setup_dasmon_listener.py clean
	rm -fR *.pyc
	rm -fR build/
	
install: check clean workflow webapp

dasmonlistener: webapp/core
	# Install DASMON listener
	python setup_dasmon_listener.py clean
	python setup_dasmon_listener.py install
	
webapp/core: workflow
	# Make sure the install directories exist
	test -d $(prefix) || mkdir -m 0755 -p $(prefix)
	test -d $(prefix)/app || mkdir -m 0755 $(prefix)/app
	test -d $(prefix)/static || mkdir -m 0755 $(prefix)/static
	test -d $(prefix)/static/web_monitor || mkdir -m 0755 $(prefix)/static/web_monitor
	
	# The following should be done with the proper apache user
	#chgrp apache $(prefix)/static/web_monitor
	#chown apache $(prefix)/static/web_monitor
	
	# Install application code
	cp reporting/manage.py $(prefix)/app
	#cp -R dasmon_listener $(prefix)/app
	cp -R reporting/report $(prefix)/app
	cp -R reporting/dasmon $(prefix)/app
	cp -R reporting/reduction $(prefix)/app
	cp -R reporting/pvmon $(prefix)/app
	cp -R reporting/file_handling $(prefix)/app
	cp -R reporting/static $(prefix)/app
	cp -R reporting/users $(prefix)/app
	cp -R reporting/templates $(prefix)/app
	cp -R reporting/reporting_app $(prefix)/app
	
	# Install apache config
	cp -R reporting/apache $(prefix)

webapp: webapp/core
	# Collect the static files and install them
	cd $(prefix)/app; python manage.py collectstatic --noinput

	# Create the database tables. The database itself must have been
	# created on the server already
ifeq ($(HAS_MIGRATIONS),1)
	@echo "Detected Django >= 1.7: Using migrations"
	# The following call only needs to be done once to create the migrations if the tables already exist
	#cd $(prefix)/app; python manage.py makemigrations report reduction dasmon pvmon file_handling users

	# Create migrations and apply them
	cd $(prefix)/app; python manage.py makemigrations
	cd $(prefix)/app; python manage.py migrate
else
	cd $(prefix)/app; python manage.py syncdb
endif
	
	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	#cd $(prefix)/app; python manage.py createcachetable webcache
	
	# Modify and copy the wsgi configuration
	#cp reporting/apache/apache_django_wsgi.conf /etc/httpd/conf.d
	
	@echo "\n\nReady to go: run apachectl restart\n"
	
.PHONY: check
.PHONY: install
.PHONY: workflow
.PHONY: webapp
.PHONY: webapp/core
.PHONY: dasmonlistener
