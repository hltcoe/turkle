# Development log #

- installed django and south in the virtual environment
- `django-admin.py startproject turkle_django`
- `python manage.py startapp hits`
- add `'hits'` to `INSTALLED_APPS` in `turkle_django/settings.py`
- added `jsonfield` to `requirements.txt`, and installed it.
- set up database
  - selected sqlite3 in `turkle_django/settings.py`
    ```python
    'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    'NAME': 'db.sqlite3',                      # Or path to database file if using sqlite3.
    ```
  - edit `hits/models.py` to add `Hit` and `AwsMTurkTemplate` models
    - many-to-many relationship between Hit and Worker objects. each of these
      is called a ...(?)
  - add `'south'` to `INSTALLED_APPS` in `turkle_django/settings.py`
  - `python manage.py syncdb`
    Did not create user for django auth system
  - `python manage.py schemamigration hits --initial`

# TODO #

*TBD*
