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

    $ sudo apt -y install apache2 mysql-server-8.0 libapache2-mod-wsgi-py3


Next, we will get SSL working with the web server using Let's Encrypt::

    $ sudo apt -y install certbot python3-certbot-apache
    $ sudo a2enmod ssl
    $ sudo systemctl restart apache2
    $ sudo certbot --apache

You should now be able to hit your web server using https.

Now, we install git and setup all the other python dependencies that we will need::

    $ sudo apt -y install git build-essential pkg-config python3-dev libmysqlclient-dev python3.12-venv


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
We put the source code in /srv/turkle, setup permissions and configure Turkle::

    $ cd /srv
    $ sudo mkdir turkle
    $ sudo groupadd webapps
    $ sudo usermod -aG webapps <your user>
    $ sudo usermod -aG webapps www-data
    $ sudo chown <your user>:webapps turkle
    $ cd turkle
    $ git clone https://github.com/hltcoe/turkle.git .
    $ sudo chown -R :webapps /srv/turkle
    $ sudo find /srv/turkle -type d -exec chmod 2750 {} \;
    $ sudo find /srv/turkle -type f -exec chmod 640 {} \;

Next, we configure the Turkle app::

    $ cd turkle_site
    $ cp example_local_settings.py local_settings.py

Use your preferred editor to open local_settings.py and do the following

 * Uncomment STATIC_ROOT and set it to /srv/turkle/static/
 * Uncomment the mysql section and set the password

We need to create a python virtual environment::

    $ cd /srv/turkle
    $ python3 -m venv venv
    $ source venv/bin/activate
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

    DocumentRoot /srv/turkle

    Alias /static /srv/turkle/static
    <Directory /srv/turkle/static>
        Require all granted
        Options -Indexes -ExecCGI -FollowSymLinks
        AllowOverride None
    </Directory>

    <Directory /srv/turkle/turkle_site>
        <Files wsgi.py>
            Require all granted
        </Files>
        Options -Indexes -ExecCGI -FollowSymLinks
        AllowOverride None
    </Directory>

    WSGIDaemonProcess turkle python-home=/srv/turkle/venv python-path=/srv/turkle
    WSGIProcessGroup turkle
    WSGIScriptAlias / /srv/turkle/turkle_site/wsgi.py

Finally, restart the web server and Turkle should be running::

    $ sudo a2enmod wsgi
    $ sudo systemctl restart apache2


Setting Up Task Expiration
----------------------------
Task assignments has expiration dates when a task goes back to the pool for
assignment to another annotator. For this to work, a cronjob has to be
configured.

Edit the crontab for www-data::

    $ sudo crontab -u www-data -e


Then add this line::

    */15 * * * * cd /srv/turkle && /srv/turkle/venv/bin/python manage.py expire_assignments 2>&1 | logger -t turkle-cron

This runs the cronjob every 15 minutes and pipes output to the syslog with the tag turkle-cron.


Database Backups
--------------------
To use mysqldump to back up the database, create a file at the path /srv/turkle/.my.cnf with this content::

    [client]
    user=turkleuser
    password=[your password here]

Set the permissions so that only you can edit and www-data can read::

    $ chmod 640 .my.cnf

Create the directory for the backups::

    $ mkdir /srv/turkle/backups

 Create a backup script at /srv/turkle/backup.sh with this content::

    #!/bin/bash

    # Set backup directory and filename
    BACKUP_DIR="/srv/turkle/backups"
    DATE=$(date +'%Y-%m-%d')
    FILENAME="turkle_backup_$DATE.sql"
    FULL_SQL_PATH="$BACKUP_DIR/$FILENAME"
    FULL_GZ_PATH="${FULL_SQL_PATH}.gz"

    # MySQL options
    MYSQL_OPTS="--defaults-file=/srv/turkle/.my.cnf --no-tablespaces"
    DB_NAME="turkle"

    # Dump the database
    mysqldump $MYSQL_OPTS "$DB_NAME" > "$FULL_SQL_PATH" && gzip "$FULL_SQL_PATH"

    # Rotate backups: keep only the 30 most recent
    cd "$BACKUP_DIR" || exit 1
    ls -1t turkle_backup_*.sql.gz | tail -n +31 | xargs -r rm --

    # log to syslog
    logger -t turkle-backup "Turkle database backup completed: $(basename "$FULL_GZ_PATH")"

Set the permissions so that www-data can run it::

    $ chmod 750 backup.sh

Finally, register it as a cron job as you did with the assignment expirations but running daily at 2 am:

    0 2 * * * /srv/turkle/backup.sh


Not covered
----------------------------------
This guide does not cover configuring SMTP for email.
