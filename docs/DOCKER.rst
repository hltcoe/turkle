Docker
======

Instead of installing Turkle and dependencies directly, you can run
Turkle as a Docker container, using the admin UI or scripts to manage
Projects and Batches of Tasks.

This repo comes with two Dockerfiles.  The file ``Dockerfile-sqlite``
uses SQLite as the database backend.  The file ``Dockerfile-MySQL`` uses
MySQL as the database backend.  The Turkle images created by both
Dockerfiles:

- listen for HTTP connections on port 8080
- use gunicorn as the WSGI HTTP server
- use Whitenoise to serve static files

Prebuilt Docker images
------------------------
With each release of Turkle, Docker images are uploaded to Docker Hub
and can be pulled down like this::

    docker pull hltcoe/turkle:latest

The above command line pulls the latest image.
A full list of versions is available on `Docker Hub`_.

SQLite Docker image
-------------------
You can build the SQLite Turkle image using::

    docker build --force-rm -t hltcoe/turkle -f Dockerfile-sqlite .

To launch a Turkle container that maps container port 8080 to Docker
host port 18080, use::

     docker run -d --name container_name -p 18080:8080 hltcoe/turkle

MySQL Docker image
------------------
The MySQL version of Turkle requires two containers - one for Turkle,
and the other for MySQL.  This multi-container Docker application is
configured and controlled by docker-compose.

The multi-container Turkle application can be built and configured
with the commands::

    docker-compose build
    docker-compose up -d
    docker-compose run turkle python manage.py createsuperuser

This will stand up a Turkle server listening on port 8080.

The database files are stored in a Docker volume named turkle_db_data.
This Docker volume persists across Docker container restarts.

To upgrade to a newer version of Turkle, shut down the application
using::

    docker-compose stop

Then build the newest version of the Turkle MySQL Docker image and
restart the application::

    docker-compose build
    docker-compose up -d

Any database migrations for the upgraded version of Turkle will be
automatically applied when the application is brought back up.

If you'd like to run the MySQL docker image on its own, look at the
environment variables set in the docker compose configuration file.

Changing the admin password
---------------------------
The SQLite Docker container has a super-user named ``admin`` with a
default password of ``admin``.  For the MySQL Docker container, the
super-user username and password are set by one of the
``docker-compose`` commands listed above.

You should change the default admin password for the SQLite Docker
container by:

- connecting to the exposed container port with a web browser (e.g. connecting to http://localhost:18080/)
- logging in with username ``admin`` and password ``admin``
- clicking on the ``Admin`` link on the top left of the screen
- clicking on the ``CHANGE PASSWORD`` link at the top right of the screen
- filling out and submitting the Change Password form

Changing the number of threads, workers and worker connections
--------------------------------------------------------------
If you want to change the number of workers, threads or the connections that a worker
accepts, you can pass environment variables to the container:

- WORKERS - The number of gunicorn workers that are started (Default: 1)
- THREADS - The number of threads started by gunicorn (Default 1)
- CONNECTIONS - The maximum number of simultaneous clients (Default: 1000)

Example::
  docker run -d -e WORKERS=3 -e THREADS=4 -e CONNECTIONS=2000 -p 8080:8080 hltcoe/turkle

Logging
------------------
The gunicorn and Turkle application logs are sent to the console and are
available using `docker logs`.

Running Dockerized Turkle with a URL prefix
-------------------------------------------
If you want to reverse proxy the Turkle container so that Turkle is not available
at the root of the web server, you need to pass an environment to the container.

If this is your reverse proxy configuration for Apache::

    <Location "/annotate">
        ProxyPass http://localhost:8080
        ProxyPassReverse http://localhost:8080
    </Location>

Then run the docker container::

    docker run -d --name [container_name] -p 8080:8080 -e TURKLE_PREFIX='annotate' hltcoe/turkle

This passes the URL prefix to the Turkle application through an environment variable.

Note that after you specify the prefix as an environment variable, you will not be able to
hit the Docker-served application directly from a web browser, but only through the reverse proxy.

Customizing the settings of Docker image
------------------------------------------
If you want to change the default settings of the Docker image for your application,
the best way to accomplish that is to build a custom Docker image that depends on turkle.
Create a Dockerfile that looks like this::

    FROM hltcoe/turkle:[version]
    COPY local_settings.py /opt/turkle/turkle_site/local_settings.py

In the `local_setting.py` file, add the settings that you want to override.
As an example, to increase the maximum template size allowed by Turkle::

    TURKLE_TEMPLATE_LIMIT = 1024

To confirm that the setting has been overridden, run the new docker image, connect to the container
with a bash shell and then use the Django shell to check the setting::

   python manage.py shell
   from django.conf import settings
   print(settings.TURKLE_TEMPLATE_LIMIT)

.. _`Docker Hub`: https://hub.docker.com/r/hltcoe/turkle/tags
