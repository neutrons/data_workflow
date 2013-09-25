prefix := /var/www/workflow

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
	@python -c "import MySQLdb" || echo "\nWARNING: MySQLdb is not installed: https://sourceforge.net/projects/mysql-python\n"
	@python -c "import psycopg2" || echo "\nWARNING: psycopg2 is not installed: http://initd.org/psycopg\n"
	@python -c "import stomp" || echo "\nERROR: somtp.py is not installed: http://code.google.com/p/stomppy\n"

workflow: check
	# Install the workflow manager, which defines the database schema
	python setup.py install

clean:
	python setup.py clean
	python setup_dasmon_listener.py clean
	rm -fR *.pyc
	rm -fR build/
	
install: clean workflow webapp
       
webapp:
	# Install DASMON listener
	python setup_dasmon_listener.py clean
	python setup_dasmon_listener.py install

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
	cp -R reporting/pvmon $(prefix)/app
	cp -R reporting/file_handling $(prefix)/app
	cp -R reporting/static $(prefix)/app
	cp -R reporting/users $(prefix)/app
	cp -R reporting/templates $(prefix)/app
	cp -R reporting/reporting_app $(prefix)/app
	
	# Install apache config
	cp -R reporting/apache $(prefix)

	# Collect the static files and install them
	cd $(prefix)/app; python manage.py collectstatic --noinput

	# Create the database tables. The database itself must have been
	# created on the server already
	cd $(prefix)/app; python manage.py syncdb
	
	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	#cd $(prefix)/app; python manage.py createcachetable webcache
	
	@echo "\n\nReady to go: run apachectl restart\n"
	
.PHONY: check
.PHONY: install
.PHONY: workflow
.PHONY: webapp
