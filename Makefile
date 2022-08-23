prefix := /var/www/workflow
PYTHON_VERSION:=3.10

# these are defined here because I couldn't figure out how to evaluate the commands
# during target execution rather then when make parses the file
# this is found by `find /opt/conda/ -name manage.py | grep reporting`
MANAGE_PY_WEBMON=/opt/conda/lib/python$(PYTHON_VERSION)/site-packages/reporting/manage.py
# this is found by `find /opt/conda -name db_init.json`
REPORT_DB_INIT=/opt/conda/lib/python$(PYTHON_VERSION)/site-packages/reporting/fixtures/db_init.json
# command to run docker compose. change this to be what you have installed
# this can be overriden on the command line
# DOCKER_COMPOSE="docker compose" make startdev
DOCKER_COMPOSE ?= docker-compose


help:
    # this nifty perl one-liner collects all comments headed by the double "#" symbols next to each target and recycles them as comments
	@perl -nle'print $& if m{^[/a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

all: wheel/dasmon wheel/webmon wheel/workflow SNSdata.tar.gz

create/conda:  ## create conda environment "webmon" with file conda_environment.yml
	conda env create --name webmon --file conda_environment.yml
	conda env update --name webmon --file conda_development.yml

create/mamba:  ## create conda environment "webmon" with file conda_environment.yml using mamba
	conda env create --name webmon python=$(PYTHON_VERSION)
	conda install --name base -c conda-forge mamba
	mamba env update --name webmon --file conda_environment.yml
	mamba env update --name webmon --file conda_development.yml

docker/pruneall: ## stop and force remove all containers, images and volumes
	docker system prune --force --all --volumes
	docker system prune --force --all --volumes

docs:  ## create HTML docs under docs/_build/html/. Requires activation of "webmon" conda environment
	@cd docs && make html SPHINXOPTS="-W --keep-going -n" && echo -e "##########\n DOCS point your browser to file://$$(pwd)/_build/html/index.html\n##########"

check: ## Check python dependencies
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

wheel/dasmon: ## create or update python wheel for service "dasmon"
	cd src/dasmon_app && if [ -d "build" ]; then chmod u+rwx -R build && rm -rf build/;fi
	cd src/dasmon_app && python -m build --no-isolation --wheel
	# verify it is correct
	cd src/dasmon_app && check-wheel-contents dist/django_nscd_dasmon-*.whl

wheel/webmon: ## create or update python wheel for service "webmon"
	cd src/webmon_app && if [ -d "build" ]; then chmod u+rwx -R build && rm -rf build/;fi
	cd src/webmon_app && python -m build --no-isolation --wheel
	# verify it is correct - ignoring duplicate file check
	cd src/webmon_app && check-wheel-contents dist/django_nscd_webmon-*.whl

wheel/workflow: ## create or update python wheel for service "workflow"
	cd src/workflow_app && if [ -d "build" ]; then chmod u+rwx -R build && rm -rf build/;fi
	cd src/workflow_app && python -m build --no-isolation --wheel
	# verify it is correct
	cd src/workflow_app && check-wheel-contents dist/django_nscd_workflow-*.whl

wheel/all:  wheel/dasmon wheel/webmon wheel/workflow ## create or update  python wheels for all servicess

wheel/clean: ## delete all the python wheels
	cd src/dasmon_app && rm -rf build/ dist/
	cd src/webmon_app && rm -rf build/ dist/
	cd src/workflow_app && rm -rf build/ dist/

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
	python $(MANAGE_PY_WEBMON) migrate --fake-initial --noinput
	python $(MANAGE_PY_WEBMON) migrate --run-syncdb --noinput

	# Prepare web monitor cache: RUN THIS ONCE BY HAND
	python $(MANAGE_PY_WEBMON) createcachetable webcache
	python $(MANAGE_PY_WEBMON) ensure_adminuser --username=${DATABASE_USER} --email='workflow@example.com' --password=${DATABASE_PASS}

	# add the stored sql proceedures
	python $(MANAGE_PY_WEBMON) add_stored_procs

	@echo "\n\nReady to go\n"

configure/load_initial_data: install/webmon
	# use fixtures to load initial data
	python $(MANAGE_PY_WEBMON) loaddata $(REPORT_DB_INIT)

SNSdata.tar.gz: ## install SNS data for testing and limited info display
	# this doesn't have explicit dependencies on the data
	# it needs to be removed when the directory changes
	tar czf SNSdata.tar.gz -C tests/data/ .

localdev/up: ## create images and start containers for local development. Doesn't update python wheels, though.
	docker-compose --file docker-compose.yml up --build

localdev/dbup:  ## dbdumpfile=database_dump_file.sql DATABASE_PASS=$(dotenv get DATABASE_PASS) make localdev/dbup
	if ! test -f "${dbdumpfile}"; then echo "dbdumpfile does not exists" && false; fi
	if test -z "${DATABASE_PASS}"; then echo "DATABASE_PASS undefined" && false; fi
	docker-compose --file docker-compose.yml stop
	docker-compose --file docker-compose.yml down --volumes
	sleep 2s
	docker-compose --file docker-compose.yml up --detach db
	sleep 10s  # give time for the database service to be ready
	docker exec -i data_workflow_db_1 /bin/bash -c "pg_restore -d workflow -U workflow" <  ${dbdumpfile} | true  # continue even if returned errors
	docker exec -i data_workflow_db_1 /bin/bash -c "psql -d workflow -U workflow -c \"ALTER ROLE workflow WITH PASSWORD '${DATABASE_PASS}';\""
	LOAD_INITIAL_DATA="false" docker-compose --file docker-compose.yml up --build

clean: wheel/clean ## delete the SNS data and all the python wheels
	rm -f SNSdata.tar.gz
	cd src/dasmon_app && rm -rf build/ dist/
	cd src/webmon_app && rm -rf build/ dist/
	cd src/workflow_app && rm -rf build/ dist/

# targets that don't create actual files
.PHONY: check
.PHONY: create/conda
.PHONY: create/mamba
.PHONY: configure/webmon
.PHONY: docker/pruneall
.PHONY: docs
.PHONE: help
.PHONY: install/dasmonlistener
.PHONY: install/webmon
.PHONY: install/workflow
.PHONY: SNSdata.tar.gz
.PHONY: localdev/up
.PHONY: localdev/dbup
.PHONY: wheel/dasmon
.PHONY: wheel/webmon
.PHONY: wheel/workflow
.PHONY: wheel/all
.PHONY: wheel/clean
