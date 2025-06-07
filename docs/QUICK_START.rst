Quick Start Guide
====================

This quick start guide is intended for the team who wants a light production
Turkle deployment. It is written for Ubuntu 24.04 but should be easy to
adapt to other linux server environments.

This guide uses:

 * Apache web server with the wsgi module
 * MySQL database
 * Ubuntu's python


Installing OS packages
----------------------------------
We assume that you have already updated your operating system with the latest updates.
First, install the web server and the database::

    $ sudo apt install apache2 mysql-server-8.0 libapache2-mod-wsgi-py3


Next, we will get SSL working with the web server using Let's Encrypt::

    $ sudo apt install certbot python3-certbot-apache
    $ sudo a2enmod ssl
    $ sudo certbot --apache

You should now be able to hit your web server using https.

Now, we install git and setup all the other python dependencies that we will need::

    $ sudo apt install git build-essential python3-dev libmysqlclient-dev python3.12-venv


Configuring the database
----------------------------------
We need to create a database and a user for Turkle using the mysql client::

    $ sudo mysql -u root

In the mysql client::

    mysql> create database turkle character set UTF8;
    mysql> create user 'turkleuser'@'localhost' identified by '<password>';
    mysql> grant all privileges on turkle.* to 'turkleuser'@'localhost';
    mysql> flush privileges;
    mysql> quit

Remember the password that you used for the next step.


Clone Turkle code and configure
----------------------------------
We put the source code in /var/www and configure Turkle::

    $ cd /var/www
    $ sudo mkdir turkle
    $ sudo chown <your user>:<your group> turkle/
    $ cd turkle
    $ git clone https://github.com/hltcoe/turkle.git .


Next, we configure the Turkle app::

    $ cd turkle_site
    $ cp example_local_settings.py local_settings.py

Use your preferred editor to open local_settings.py and do the following

 * Uncomment STATIC_ROOT and set it to /var/www/turkle/static/
 * Uncomment the mysql section and set the password

We need to create a python virtual environment::

    $ cd /var/www/turkle
    $ python -m venv .venv
    $ source .venv/bin/activate
    $ pip install -U pip wheel
    $ pip install mysqlclient
    $ pip install -r requirements.txt


Install Turkle
----------------------------------
We populate the database and configure the web server::

    $ python manage.py migrate
    $ python manage.py createsuperuser
    $ python manage.py collectstatic

We have to tell Apache to use wsgi to run Turkle by sudoing your favorite editor
to update /etc/apache2/sites-available/000-default-le-ssl.conf and adding these
lines to the VirtualHost configuration::

    DocumentRoot /var/www/turkle

    Alias /static /var/www/turkle/static
    <Directory /var/www/turkle/static>
        Require all granted
        Options -Indexes -ExecCGI -FollowSymLinks
        AllowOverride None
    </Directory>

    <Directory /var/www/turkle/turkle_site>
        <Files wsgi.py>
            Require all granted
        </Files>
        Options -Indexes -ExecCGI -FollowSymLinks
        AllowOverride None
    </Directory>

    WSGIDaemonProcess turkle python-home=/var/www/turkle/.venv python-path=/var/www/turkle
    WSGIProcessGroup turkle
    WSGIScriptAlias / /var/www/turkle/turkle_site/wsgi.py

Finally, restart the web server and Turkle should be running::

    $ sudo a2enmod wsgi
    $ sudo systemctl restart apache2


Not covered
----------------------------------
This guide does not cover setting a mail transfer agent for email support
or configuring a cron job for regularly creating back-ups.
