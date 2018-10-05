FROM centos:7
MAINTAINER Tom Lippincott <tom.lippincott@gmail.com>
LABEL Description="Image for running a Turkle interface"

RUN yum install epel-release -y && \
    yum install python-pip patch git -y && \
    yum clean all -y

COPY hits /opt/turkle/hits
COPY manage.py /opt/turkle/manage.py
COPY requirements.txt /opt/turkle/requirements.txt
COPY scripts /opt/turkle/scripts
COPY turkle /opt/turkle/turkle

WORKDIR /opt/turkle

RUN patch turkle/settings.py scripts/enable_whitenoise.patch

RUN pip install --upgrade -r requirements.txt
RUN pip install gunicorn whitenoise

RUN python manage.py collectstatic
RUN python manage.py migrate

RUN scripts/create_turkle_admin.sh

VOLUME /opt/turkle

EXPOSE 8080

CMD gunicorn --bind 0.0.0.0:8080 turkle.wsgi
