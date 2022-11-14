Turkle
======

Run a clone of Amazon's Mechanical **Turk** service in your **l**\ocal
**e**\nvironment.

Turkle is implemented as a Django_-based web application that can
be deployed on your local network or hosted on a public server.  It
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

Turkle Workflow Overview
------------------------

Turkle provides a Task-oriented interface for **Workers**, and an
administrative interface for **Requesters**.

Requesters create **Projects** that have an HTML template with a form body.
The HTML template defines the user interface for collecting annotations. 
:doc:`Documentation on creating templates <TEMPLATE-GUIDE>` is found
in the docs directory.

Once a Project has been created, a Requester can create a **Batch** of
**Tasks** for Workers by uploading a CSV file. The CSV file defines 
the data to be annotated. A separate Task is generated for each row 
in the CSV file (excluding the header).  When a Batch is created, 
the Requester can specify how many **Assignments** per Task they need.
Each Worker is limited to one Assignment per Task. Requesters can 
download completed annotations as CSV files.
:doc:`Further documentation for Requesters <REQUESTERS>` is found 
in the docs directory.


Installation
============

Turkle works with Python 3.6+.

This Installation section covers the quickest and easiest way to use
Turkle with a handful of users on your local network by using the
Django development web server with the SQLite database backend.

If you want to use Turkle with more than a handful of Workers or host
Turkle on a public webserver, it is **strongly recommended** that you
use a scalable webserver and database backend.  Please see the
documentation of production deployments included in the 
:doc:`Administration guide <ADMINISTRATION>` in the docs directory.

If you would like to use Turkle in a Docker container, see the 
:doc:`Docker guide <DOCKER>`.

If you would like to add Turkle to an existing Django-based site,
see the :doc:`Django app <APP>` guide.


Dependencies
------------

Turkle depends on the packages listed in ``requirements.txt``.
If the packages are not already installed in your environment, and you have
an internet connection, then you can run the following command to install
the required Python packages::

    pip install -r requirements.txt

Using a virtual environment has the advantage of keeping the dependencies
for this project separate from other projects. The actual syntax depends
on what virtual environment package you are using, but here is an example::

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

One-time Configuration Steps
----------------------------

After the dependencies have been installed, create and initialize the
database::

    python manage.py migrate

Next, create an admin account::

    python manage.py createsuperuser

Upgrading
---------

After copying over the new code, update to the new Python dependencies in your virtual environment::

    pip install -r requirements.txt

Then run the migrate script to update your database::

    python manage.py migrate

If serving the static files through a web server like Apache or nginx, collect the static assets::

    python manage.py collectstatic


Usage
=====


Running the development server
------------------------------

Start the development web server on port 8000 using::

    python manage.py runserver 0.0.0.0:8000

Developers
==========

Running tests
-------------

::

    python manage.py test

Style Guideline
---------------

Python code should be formatted according to `PEP 8`_.

Building Docs
-------------
The Turkle documentation is built with Sphinx.
To install::

    pip install sphinx sphinx-rtd-theme

To build from the docs directory::

    make html


Release process
---------------

 1. Set version number in ``turkle/__init__.py``
 2. Update ``CHANGELOG.md``
 3. Commit and tag version
 4. Deploy to PyPI
 
.. _Django: https://www.djangoproject.com
.. _`PEP 8`: https://www.python.org/dev/peps/pep-0008/
