FROM centos:7.6.1810

RUN yum install -y epel-release; \
    yum groupinstall -y 'development tools'; \
    yum install -y openldap-devel python-pip python-devel postgresql postgresql-devel; \
    yum clean all; rm -rf /var/cache/yum

WORKDIR /usr/src/data_workflow

COPY ./src/. .
COPY ./README.md .
RUN pip install --no-cache-dir -r requirements.txt;
