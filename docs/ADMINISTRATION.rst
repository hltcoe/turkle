Administration Guide
====================

While Turkle can run out of the box using the Django development web server
and a SQLite database, we recommend using a scalable database and a production
quality WSGI HTTP server. This guide describes the steps of running a production
Turkle site.

Topics:

 * Web server
 * Database
 * Cron
 * Email

Configuration changes should be made by creating a
``turkle_site/local_settings.py`` file.  Configuration changes in this
file override the default configuration settings in
``turkle_site/settings.py``.  The file
``turkle_site/example_local_settings.py`` contains some examples of how
to customize local settings.

Production Webserver Configuration
----------------------------------

Configuring Static Files
````````````````````````

In a production environment, static files should be served by a web
server and not by a Django web application.  In ``turkle_site/local_settings.py``, you
will need to set the STATIC_ROOT directory to the location where you
want to store the static files, e.g.::

    STATIC_ROOT = "/var/www/example.com/static/"

You should then run the ``collectstatic`` management command::

    $ python manage.py collectstatic

which will copy all static files for Turkle into the STATIC_ROOT
directory.

The `Django static files HOWTO`_
provides more details about how Django handles static files in
production environments.

Running with Gunicorn
`````````````````````

Gunicorn_ is a Python WSGI HTTP server that can
be installed with pip::

    pip install gunicorn

Gunicorn can be run from Turkle's base directory using::

    gunicorn --bind 0.0.0.0:8000 turkle_site.wsgi

Common Gunicorn runtime options are available in the
`Running Gunicorn documentation`_.

The Gunicorn command above serves Turkle's web pages on port 8000 but
not the static files like CSS and JavaScript.  For serious production
uses of Turkle, the best option is to use a proxy server (like Apache
or nginx) to serve the static files. More details on that below.

If you don't want to set up a proxy server, you can use
Whitenoise_ to serve the static files.  Install it using::

    pip install whitenoise

and then enable Whitenoise in ``turkle_site/local_settings.py`` by
adding the appropriate string to the MIDDLEWARE list::

    MIDDLEWARE = (
        'whitenoise.middleware.WhiteNoiseMiddleware',
    ) + MIDDLEWARE

Note that you need to follow the previous instructions on configuring ``STATIC_ROOT``
before running with whitenoise.

Apache as a reverse proxy
`````````````````````````

To use Apache as the proxy server, enable proxying: ``a2enmod proxy_http``.
Then edit the configuration of your site to include the proxy information::

    ProxyRequests Off
    ProxyPass /static/ !
    ProxyPass / http://localhost:5000/
    ProxyPassReverse / http://localhost:5000/

Apache will look in its default location for the static directory so you'll need to create
a symbolic link (more convenient) or copy the files (safer).
After starting Gunicorn and restarting Apache with the new configuration, you should
be able to view the site at http://localhost/ or whatever the appropriate host name is.

Instructions for using Gunicorn with nginx are found on its `deploy page`_.
You will still need to configure nginx to serve the static files as we did with Apache.

Emails behind proxy
```````````````````
If your site has been configured for emails, the emails for password resets
will use the localhost URL rather than the external URL.
To configure this, set this variable in the local_settings.py file::

    USE_X_FORWARDED_HOST = True

This will cause Django to pick up the HTTP_X_FORWARDED_HOST header
when populating the protocol, domain, and site_name for the emails.

Production Database Configuration
---------------------------------

MySQL
`````

First, you need to install the Python mysqlclient library::

    pip install mysqlclient

Note that this requires development headers for MySQL and Python to be installed.
The method for installing these depends on your operating system.

Second, create a database and database user for Turkle. In the examples below,
we are calling the database ``turkle`` and the user ``turkleuser`` with the password ``password``.
Log into the MySQL client and run the following commands::

    CREATE DATABASE turkle CHARACTER SET UTF8;
    CREATE USER turkleuser@localhost IDENTIFIED BY 'password';
    GRANT ALL PRIVILEGES ON turkle.* TO turkleuser@localhost;
    FLUSH PRIVILEGES;

Third, update Turkle's settings to point at this database::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'turkle',
            'USER': 'turkleuser',
            'PASSWORD': 'password',
            'HOST': 'localhost'
        }
    }

The last step is running the Turkle install steps (migrate and createsuperuser).

PostgreSQL
``````````

First, you need to install the Python PostgreSQL adapter::

    pip install psycopg2

Note that this requires development headers for PostgreSQL and Python to be installed.
The method for installing these depends on your operating system.

Second, create a database and database user for Turkle. In the examples below,
we are calling the database ``turkle`` and the user ``turkleuser`` with the password ``password``.
Log into the psql client and run the following commands::

    CREATE DATABASE turkle;
    CREATE USER turkleuser WITH PASSWORD 'password';
    ALTER ROLE turkleuser SET client_encoding TO 'utf8';
    GRANT ALL PRIVILEGES ON DATABASE turkle TO turkleuser;

Third, update Turkle's settings to point at this database::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'turkle',
            'USER': 'turkleuser',
            'PASSWORD': 'password',
            'HOST': 'localhost'
        }
    }

The last step is running the Turkle install steps (migrate and
createsuperuser) described in the "One-time Configuration Steps"
section above.

Database Backups
----------------

You will likely want to add a cron job that dumps the database each
hour or day using the dump command for your database::

    @hourly /path/to/my/script.sh

Cron
----

Task Assignments have expiration dates. The expired assignments are deleted
when the expire_assignments command is run. This can be done manually through
the administration pages or by running the command::

    python manage.py expire_assignments

For production sites, we recommend that you configure a cron job to delete
assignments regularly. The ``docker-config/`` directory contains a 
``turkle.crontab`` file that can be used to periodically run the script 
using cron.  The method for configuring a cron job depends on your 
operating system.

The Turkle Docker containers are configured to use cron to
automatically delete expired Task Assignments.

Email Configuration
-------------------

Turkle can send password reset emails if your server is configured to deliver emails.
By default, the links to the password reset page are hidden.
To enable, edit the ``turkle_site/local_settings.py`` file and set the variable ``TURKLE_EMAIL_ENABLED`` to ``True``.
You will need to add a section to ``turkle_site/local_settings.py`` for
configuring a Mail Transfer Agent (MTA).  The
``turkle_site/example_local_settings.py`` file contains a (commented out) section with
sample settings for configuring an MTA with Django.  For more details
about configuring an MTA, consult the Django docs.

Logging Configuration
---------------------

Before running Turkle in a production environment, logging must be configured 
in the ``turkle_site/local_settings.py`` file. There is a sample logging
configuration in the ``turkle_site/example_local_settings.py``
file if an administrator wants to receive emails if HTTP 500 errors occur.

.. _`Django static files HOWTO`: https://docs.djangoproject.com/en/2.2/howto/static-files/deployment/
.. _Gunicorn: https://gunicorn.org
.. _`Running Gunicorn documentation`: http://docs.gunicorn.org/en/stable/run.html
.. _Whitenoise: https://pypi.org/project/whitenoise/
.. _`deploy page`: http://docs.gunicorn.org/en/latest/deploy.html
