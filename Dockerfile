FROM centos:7
MAINTAINER Tom Lippincott <tom.lippincott@gmail.com>
LABEL Description="Image for running a Turkle interface"

RUN yum install epel-release -y && \
    yum install python-pip git -y && \
    yum clean all -y

COPY . /opt/turkle

WORKDIR /opt/turkle

RUN pip install --upgrade -r requirements.txt

EXPOSE 8080

CMD python manage.py runserver 0.0.0.0:8080
