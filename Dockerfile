FROM centos:7
MAINTAINER Craig Harman <craig@craigharman.net>
LABEL Description="Image for running a Turkle interface"

RUN yum install epel-release -y && \
    yum install crontabs git patch python36 python36-pip -y && \
    yum clean all -y

WORKDIR /opt/turkle

COPY requirements.txt /opt/turkle/requirements.txt
RUN pip3.6 install --upgrade -r requirements.txt
RUN pip3.6 install gunicorn whitenoise

COPY turkle /opt/turkle/turkle
COPY manage.py /opt/turkle/manage.py
COPY scripts /opt/turkle/scripts
COPY turkle_site /opt/turkle/turkle_site
COPY docker-config/create_turkle_admin.sh /opt/turkle/create_turkle_admin.sh

COPY docker-config/turkle.crontab /etc/cron.d/turkle
RUN crontab /etc/cron.d/turkle

ENV TURKLE_DOCKER=1
RUN python3.6 manage.py collectstatic
RUN python3.6 manage.py migrate
RUN ./create_turkle_admin.sh

VOLUME /opt/turkle

EXPOSE 8080

CMD crond && gunicorn --env TURKLE_DOCKER=1 --bind 0.0.0.0:8080 turkle_site.wsgi
