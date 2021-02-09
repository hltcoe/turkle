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

Full documentation is available at `Read the Docs`_.

.. _Django: https://www.djangoproject.com
.. _`Read the Docs`: https://turkle.readthedocs.io/
