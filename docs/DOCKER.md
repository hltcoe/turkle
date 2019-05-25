# Docker

Instead of installing Turkle and dependencies directly, you can run
Turkle as a Docker container, using the admin UI or scripts to manage
Projects and Batches of Tasks.

This repo comes with two Dockerfiles.  The default file `Dockerfile`
uses SQLite as the database backend.  The file `Dockerfile-MySQL` uses
MySQL as the database backend.  The Turkle images created by both
Dockerfiles:

- listen for HTTP connections on port 8080
- use gunicorn as the WSGI HTTP server
- use Whitenoise to serve static files

## SQLite Docker image ##

You can build the SQLite Turkle image using:

```bash
docker build --force-rm -t hltcoe/turkle .
```

To launch a Turkle container that maps container port 8080 to Docker
host port 18080, use:

```bash
docker run -d --name container_name -p 18080:8080 hltcoe/turkle
```

## MySQL Docker image ##

The MySQL version of Turkle requires two containers - one for Turkle,
and the other for MySQL.  This multi-container Docker application is
configured and controlled by docker-compose.

The multi-container Turkle application can be built and configured
with the commands:

    docker-compose build
    docker-compose up -d
    docker-compose run turkle python3.6 manage.py migrate --noinput
    docker-compose run turkle python3.6 manage.py createsuperuser

This will stand up a Turkle server listening on port 8080.
The database files are stored in a docker volume called turkle_db_data.

## Changing the admin password ##

The SQLite Docker container has a super-user named `admin` with a
default password of `admin`.  For the MySQL Docker container, the
super-user username and password are set by one of the
`docker-compose` commands listed above.

You should change the default admin password for the SQLite Docker
container by:

- connecting to the exposed container port with a web browser (e.g. connecting to http://localhost:18080/)
- logging in with username `admin` and password `admin`
- clicking on the `Admin` link on the top left of the screen
- clicking on the `CHANGE PASSWORD` link at the top right of the screen
- filling out and submitting the Change Password form

## Running Dockerized Turkle with a URL prefix ##

If you want to reverse proxy the Turkle container so that Turkle is not available
at the root of the web server, you need to pass an environment to the container.

If this is your reverse proxy configuration for Apache:

```
<Location "/annotate">
    ProxyPass http://localhost:8080
    ProxyPassReverse http://localhost:8080
</Location>
```

Then run the docker container:

```bash
docker run -d --name [container_name] -p 8080:8080 -e TURKLE_PREFIX='annotate' hltcoe/turkle
```

This passes the URL prefix to the Turkle application through an environment variable.
Note that the application will be functional when directly hitting the application server.
If that is required, use `SCRIPT_NAME` with your own Docker image.
