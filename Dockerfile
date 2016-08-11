FROM centos:7
MAINTAINER Tom Lippincott <tom.lippincott@gmail.com>
LABEL Description="Image for running a Turkle interface"

RUN yum install epel-release -y && \
    yum install python-pip git -y && \
    yum clean all -y

RUN pip install --upgrade jsonfield unicodecsv django==1.9 django-nose

COPY . /opt/turkle

EXPOSE 8080

WORKDIR /opt/turkle

CMD python manage.py runserver 0.0.0.0:8080
