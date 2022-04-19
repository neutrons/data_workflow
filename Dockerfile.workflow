FROM continuumio/miniconda3:4.10.3p1

COPY conda_environment.yml .
RUN conda env update --name base --file conda_environment.yml

WORKDIR /usr/src/data_workflow

# copy the necessary wheels and the Makefile which knows the dependency order
COPY ./src/workflow_app/dist/django_nscd_workflow-*-none-any.whl .
COPY ./Makefile .

# move the entry-point into the volume
COPY ./src/workflow_app/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
RUN chmod +x /usr/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]
