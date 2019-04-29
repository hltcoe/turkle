# Turkle #

Run a clone of Amazon's Mechanical **Turk** service in your **l**ocal
**e**nvironment.

Turkle is implemented as a
[Django](https://www.djangoproject.com)-based web application that can
be deployed on your local network, or hosted on a public server.  It
is compatible with Human Intelligence Tasks (HITs) from Amazon
Mechanical Turk.  Turkle can use the same HTML Task template files and
CSV files as the MTurk requester web GUI.  The results of the Tasks
completed by the workers can be exported to CSV files.

Turkle's features include:

- Authentication support for Users
- Projects can be restricted to Users who are members of a particular Group
- Projects can be configured so that each Task needs to be completed by
  multiple Workers (redundant annotations)
- An admin GUI for managing Users, Groups, Projects, and Batches of Tasks
- Scripts to automate the creation of Users, Projects, and Batches of Tasks
- Docker images using the SQLite and MySQL database backends

## Turkle Workflow Overview ##

Turkle provides a Task-oriented interface for **Workers**, and an
administrative interface for **Requesters**.

Requesters create **Projects** that have an HTML template with a form.
Once a Project has been created, requesters can create a **Batch** of
**Tasks** by uploading a CSV file.  A separate Task is generated for
each row in the CSV file (excluding the header).  When a Batch is
created, the Requester can specify how many **Assignments** per Task
they need.  Each Worker is limited to one Assignment per Task.

The HTML template will include template variables, which have the form
`${variable_name}`.  The CSV files used to create Task Batches include
a header row with the names of the template variables.  When a Worker
visits a Task web page, the variables in the HTML template will be
replaced with the corresponding values from a row of the CSV file.

If a Project's HTML template file uses template variables named
`${foo}` and `${bar}`:

``` html
  <p>The variable 'foo' has the value: ${foo}</p>
  <p>The variable 'bar' has the value: ${bar}</p>
  <input type="text" name="my_input" />
```

then the CSV input file's header row should have fields named 'foo'
and 'bar':

    "foo","bar"
	"1","one"
	"2","two"

When a Worker views the web page for a Task or Task Assignment, the
template variables will be replaced with the corresponding values from
a row of the CSV file:

``` html
  <p>The variable 'foo' has the value: 1</p>
  <p>The variable 'bar' has the value: one</p>
  <input type="text" name="my_input" />
```

The HTML template can include any HTML form input fields, such as text
boxes, radio buttons, and check boxes.  When the Worker submits a Task
Assignment, the values of the form fields are saved to the Turkle database.

Task Assignment data can be exported to CSV files.  Each row of the
CSV results file contains the template variable input fields, the
Worker-submitted form fields, and some metadata fields.  For each
template variable `${foo}`, the CSV file will contain a column named
`Input.foo`.  For each submitted form field named `bar`, the CSV file
will contain a column named `Answer.bar`.  The CSV file will also have
the fields:

- `HITId` - Task ID
- `HITTypeId` - Project ID
- `Title` - Project name
- `CreationTime` - Time when the Task was created from CSV input file
- `MaxAssignments` - Number of *requested* Assignments per Task
- `AssignmentDurationInSeconds` - Amount of time before a Task
  Assignment expires
- `AssignmentId` - Task Assignment ID
- `WorkerId`
- `AcceptTime` - Time when User accepted an Assignment for a Task
- `SubmitTime` - Time when User submitted an Assignment for a Task
- `WorkTimeInSeconds` - Length of time between when User accepted
   a Task Assignment and when User submitted that Assignment
- `Turkle.Username` - Username of User who completed Assignment


# Installation #

Turkle works with Python 3.5+.

This Installation section covers the quickest and easiest way to use
Turkle with a handful of users on your local network - using the
Django development web server with the SQLite database backend.

If you want to use Turkle with more than a handful of Workers or host
Turkle on a public webserver, it is **strongly recommended** that you
use a more scalable webserver and database backend.  Please see the
"Production deployment" section below for additional installation
details not covered in this section.

If you would like to use Turkle in a Docker container, see the "Docker
usage" section later in this document.


## Dependencies ##

Turkle depends on the packages listed in `requirements.txt`.
If the packages are not already installed in your environment, and you have
an internet connection, then you can run the following command to install
the required Python packages:

```bash
pip install -r requirements.txt
```

Using a virtual environment has the advantage of keeping the dependencies
for this project separate from other projects. The actual syntax depends
on what virtual environment package you are using, but here is an example:

```bash
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## One-time Configuration Steps ##

After the dependencies have been installed, create and initialize the
database:

```bash
python manage.py migrate
```

Next, create an admin account:

```bash
python manage.py createsuperuser
```

## Configuring automatic expiration of Task Assignments ##

If a user takes a Task Assignment but never submits the Assignment,
the Task Assignment eventually expires.  The expiration time is
determined by a Batch-level parameter called "Allotted assignment
time".  Expired Task Assignments can be deleted using the "Expire
Abandoned Assignments" button in the Admin UI, or by running the
script:

```bash
python manage.py expire_assignments
```

The `docker-config/` directory contains a `turkle.crontab` file that
can be used to periodically run the script using cron.  The method for
configuring a cron job depends on your operating system.

The Turkle Docker containers are configured to use cron to
automatically delete expired Task Assignments.


# Usage


## Running the development server ##

Start the development web server on port 8000 using:

```bash
python manage.py runserver 0.0.0.0:8000
```


## Creating user accounts ##

### Using the admin UI

* Login with an admin account
* Select `Admin` from the navigation header
* In the `Users` row, click the `Add` button, fill out the form and submit

![Turkle admin UI](docs/images/Turkle_admin.png)

### Using the scripts
The `scripts/add_user.py` script adds a single user. Run it with the `-h` option for details.

The `script/import_users.py` script reads a CSV file to add users to Turkle.
The file must be formatted like:
```
username1,password1
username2,password2
```

To support password resets, add an additional column for email address:
```
username1,password1,email1@example.com
username2,password2,email2@example.com
```

## Creating HTML Templates ##

The HTML template code that you write should not be a complete HTML
document with `head` and `body` tags.  Turkle renders the page for a
Task by inserting your HTML template code into an HTML `form` element
in the body of an HTML document.  The document looks like this:

``` html
<!DOCTYPE html>
<html>
  <head>
    <title></title>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
  </head>
  <body>
    <form name="mturk_form" method="post" id="mturk_form"
          target="_parent" action='/some/submit/url'>
      <!-- YOUR HTML IS INSERTED HERE -->
      {% if not project_html_template.has_submit_button %}
      <input type="submit" id="submitButton" value="Submit" />
      {% endif %}
    </form>
  </body>
</html>
```

Turkle displays the combined HTML document in an iframe, so that your
code is isolated from any CSS and JavaScript libraries used by the
Turkle UI.  If your Project's HTML template code does not include an
HTML 'Submit' button, then Turkle will add a 'Submit' button to the
combined document.

There are example HTML and CSV files in the `examples` directory:

- `translate_minimal.html` uses just HTML elements without any
  JavaScript.  The corresponding CSV file is `translate_two_cities.csv`.
- `translate_validate.html` uses third-party JavaScript libraries to
  perform form validation.  The corresponding CSV file is
  `translate_two_cities.csv`.
- `lda-lemmas.html` is a more complicated example that uses custom
  JavaScript to dynamically generate HTML elements and CSV files that
  store data structures as JSON strings.  The corresponding CSV files
  are `lda-lemmas-0.csv` and `lda-lemmas-1.csv`.


## Creating Projects and Publishing Batches of Tasks ##

### Using the admin UI

Create a Project:

* Login with an admin account
* Select `Admin` from the navigation header
* In the `Projects` row, click the `Add` button, fill out the form
  and submit

Publish a Batch of Tasks:

* Click on the `Turkle administration` link in the top-left corner of
  the screen
* In the `Batches` row, click the `Add` button to go to the Add Batch
  page.  Fill out the form on this page (selecting a Project and
  uploading a CSV file), and then click `Review Batch`.  The Review
  Batch page lets you browse through all Tasks in the Batch, and
  verify that the Project's HTML Template functions as expected.  You
  can click `Publish Batch` if everything works, or `Cancel Batch` if
  the template needs to be updated.


### Using the scripts
With an HTML template file and a CSV Batch file, use the
`script/upload_tasks.py` script to:

- create a new Project using the HTML template file, and
- publish a Batch of Tasks using the rows of the CSV file

If you have already created a Project using an HTML template, you
should use the admin UI to publish additional Batches of Tasks.

## Downloading a Batch of completed Task Assignments ##

### Using the admin UI

* Click on the `Turkle administration` link in the top-left corner of
  the screen
* Click on the `Batches` link to view a table of all Batches
* Click on the `Download CSV results file` link for the Batch you are
  interested in

![Batch list](docs/images/Batch_list.png)

### Using the scripts
The `scripts/download_results.py` script downloads all Tasks that have been completed
into a directory that the user selects.


# Production deployment

While Turkle can run with the default SQLite database and Django development web server,
for anything more than a few annotators, we recommend using a scalable database and
a production quality WSGI HTTP server.

To run on port 80 of your server, a common configuration would be a web server like
Apache or nginx as a proxy server with a Python HTTP server like Gunicorn behind it.

## email Configuration

Turkle can send password reset emails if your server is configured to deliver emails.
By default, the links to the password reset page are hidden.
To enable, edit the `turkle_site/settings.py` file and set the variable `TURKLE_EMAIL_ENABLED` to `True`.
Then edit the section directly below to configure connecting to the Mail Transfer Agent (MTA).

## Logging Configuration

The Turkle application does not log any internal state. There is a sample logging
configuration in the settings file if an administrator wants to receive emails
if HTTP 500 errors occur.

## Production Database Configuration

### MySQL

First, you need to install the Python mysqlclient library:

```bash
pip install mysqlclient
```
Note that this requires development headers for MySQL and Python to be installed.
The method for installing these depends on your operating system.

Second, create a database and database user for Turkle. In the examples below,
we are calling the database `turkle` and the user `turkleuser` with the password `password`.
Log into the MySQL client and run the following commands:

```sql
CREATE DATABASE turkle CHARACTER SET UTF8;
CREATE USER turkleuser@localhost IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON turkle.* TO turkleuser@localhost;
FLUSH PRIVILEGES;
```

Third, update Turkle's settings to point at this database:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'turkle',
        'USER': 'turkleuser',
        'PASSWORD': 'password',
        'HOST': 'localhost'
    }
}
```
The last step is running the Turkle install steps (migrate and createsuperuser).

### PostgreSQL

First, you need to install the Python PostgreSQL adapter:

```bash
pip install psycopg2
```
Note that this requires development headers for PostgreSQL and Python to be installed.
The method for installing these depends on your operating system.

Second, create a database and database user for Turkle. In the examples below,
we are calling the database `turkle` and the user `turkleuser` with the password `password`.
Log into the psql client and run the following commands:

```sql
CREATE DATABASE turkle;
CREATE USER turkleuser WITH PASSWORD 'password';
ALTER ROLE turkleuser SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE turkle TO turkleuser;
```

Third, update Turkle's settings to point at this database:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'turkle',
        'USER': 'turkleuser',
        'PASSWORD': 'password',
        'HOST': 'localhost'
    }
}
```
The last step is running the Turkle install steps (migrate and
createsuperuser) described in the "One-time Configuration Steps"
section above.

## Database Backups

To backup the database, edit the configuration in settings.py for backups.
Then run the command:

```bash
python manage.py dbbackup
```

To restore the database:

```bash
python manage.py dbrestore -i [path to dump file]
```

There is [documentation](https://django-dbbackup.readthedocs.io/en/stable/commands.html) available on the these commands
including how to automatically compress the dump file or remove old dump files.

You will likely want to add a cron job that dumps the database each hour or day.

```
@hourly /path/to/my/script.sh
```

The script needs to access the python running Turkle:

```bash
#!/bin/bash

source /path/to/venv/bin/activate
cd /path/to/turkle

python manage.py dbbackup -c -z
```

## Production Webserver Configuration

### Configuring Static Files

In a production environment, static files should be served by a web
server and not by a Django web application.  In `settings.py`, you
will need to set the STATIC_ROOT directory to the location where you
want to store the static files, e.g.:

``` python
STATIC_ROOT = "/var/www/example.com/static/"
```

You should then run the `collectstatic` management command:

``` shell
$ python manage.py collectstatic
```

which will copy all static files for Turkle into the STATIC_ROOT
directory.

The [Django static files HOWTO](https://docs.djangoproject.com/en/1.11/howto/static-files/deployment/)
provides more details about how Django handles static files in
production environments.

### Running with Gunicorn

[Gunicorn](https://gunicorn.org) is a Python WSGI HTTP server that can
be installed with pip:

```bash
pip install gunicorn
```

Gunicorn can be run from Turkle's base directory using:

```bash
gunicorn --bind 0.0.0.0:8000 turkle_site.wsgi
```

Common Gunicorn runtime options are available in the
[Running Gunicorn documentation](http://docs.gunicorn.org/en/stable/run.html).

The Gunicorn command above serves Turkle's web pages on port 8000 but
not the static files like CSS and JavaScript.  For serious production
uses of Turkle, the best option is to use a proxy server (like Apache
or nginx) to serve the static files. More details on that below.

If you don't want to set up a proxy server, you can use
[Whitenoise](https://pypi.org/project/whitenoise/) to serve the static
files.  Install it using:

```bash
pip install whitenoise
```

and then enable Whitenoise in `turkle_site/settings.py` by adding this line
to the MIDDLEWARE section:

``` python
'whitenoise.middleware.WhiteNoiseMiddleware',
```

Note that you need to follow the previous instructions on configuring static files
before running with whitenoise.

### Apache as a reverse proxy

To use Apache as the proxy server, enable proxying: `a2enmod proxy_http`.
Then edit the configuration of your site to include the proxy information:

```
ProxyRequests Off
ProxyPass /static/ !
ProxyPass / http://localhost:5000/
ProxyPassReverse / http://localhost:5000/
```

Apache will look in its default location for the static directory so you'll need to create
a symbolic link (more convenient) or copy the files (safer).
After starting Gunicorn and restarting Apache with the new configuration, you should
be able to view the site at http://localhost/ or whatever the appropriate host name is.

Instructions for using Gunicorn with nginx are found on its [deploy page](http://docs.gunicorn.org/en/latest/deploy.html).
You will still need to configure nginx to serve the static files as we did with Apache.


# Docker usage

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


## Using scripts with Dockerized Turkle ##

The scripts for creating users (`scripts/add_user.py`,
`scripts/import_users.py`), creating Projects and publishing Batches
of Tasks (`scripts/upload_tasks.py`), and downloading completed Task
Assignments (`scripts/download_results.py`) work the same whether
Turkle is running in a Docker container or on the local host.
