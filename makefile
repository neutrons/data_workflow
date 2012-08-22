prefix := /var/www/workflow

all:
	echo "Run make install to install the workflow manager and the web app"
	
install:
	# Make sure the install directories exist
	test -d $(prefix) || mkdir -m 0755 -p $(prefix)
	test -d $(prefix)/app || mkdir -m 0755 $(prefix)/app
	test -d $(prefix)/static || mkdir -m 0755 $(prefix)/static
	
	# Install application code
	cp reporting/manage.py $(prefix)/app
	cp -R reporting/report $(prefix)/app
	cp -R reporting/static $(prefix)/app
	cp -R reporting/templates $(prefix)/app
	cp -R reporting/reporting_app $(prefix)/app
	
	# Install apache config
	cp -R reporting/apache $(prefix)

	# Collect the static files and install them
	cd $(prefix)/app; python manage.py collectstatic

	# Create the database tables. The database itself must have been
	# created on the server already
	cd $(prefix)/app; python manage.py syncdb
	
	
	