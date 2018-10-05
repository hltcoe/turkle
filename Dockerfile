FROM centos:7
MAINTAINER Craig Harman <craig@craigharman.net>
LABEL Description="Image for running a Turkle interface"

RUN yum install epel-release -y && \
    yum install python-pip git crontabs -y && \
    yum clean all -y

WORKDIR /opt/turkle

COPY requirements.txt /opt/turkle/requirements.txt
RUN pip install --upgrade -r requirements.txt

COPY hits /opt/turkle/hits
COPY manage.py /opt/turkle/manage.py
COPY scripts /opt/turkle/scripts
COPY turkle /opt/turkle/turkle

COPY docker-config/turkle.crontab /etc/cron.d/turkle
RUN crontab /etc/cron.d/turkle

RUN python manage.py migrate
RUN scripts/create_turkle_admin.sh

VOLUME /opt/turkle

EXPOSE 8080

CMD crond && python manage.py runserver 0.0.0.0:8080
