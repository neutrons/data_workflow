FROM continuumio/miniconda3

COPY conda_environment.yml .
RUN conda env update --name base --file conda_environment.yml

WORKDIR /usr/src/data_workflow

# the next line copies in all of the python source rather than just what is needed
COPY ./src/. .
COPY README.md .

# Only do this for testing, comment out for production
RUN echo 'brokers = [("activemq", 61613)]' > workflow/database/local_settings.py

# move the entry-point into the volume
COPY ./src/workflow/docker-entrypoint.sh /usr/bin/docker-entrypoint.sh
RUN chmod +x /usr/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/bin/docker-entrypoint.sh"]