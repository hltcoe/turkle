Run a clone of Amazon's Mechanical **Turk** service in your **l**ocal
**e**nvironment.

## Initial setup ##

```bash
git clone https://github.com/lukeorland/turkle.git
cd turkle
virtualenv --distribute venv
source venv/bin/activate
pip install -U distribute
pip install -r requirements.txt
```

TODO: instructions for installing from an extracted bundle that is distributed
along with the required eggs.

## Dependencies ##

- the packages listed in `requirements.txt`

## Development log ##

- installed django and south in the virtual environment
- `django-admin.py startproject turkle`
- `python manage.py startapp hits`
- add `'hits'` to `INSTALLED_APPS` in `turkle/settings.py`
- added `jsonfield` to `requirements.txt`, and installed it.
- set up database
  - selected sqlite3 in `turkle/settings.py`
    ```python
    'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
    'NAME': 'db.sqlite3',                      # Or path to database file if using sqlite3.
    ```
  - edit `hits/models.py` to add `Hit` and `AwsMTurkTemplate` models
    - many-to-many relationship between Hit and Worker objects. each of these
      is called a ...(?)
  - add `'south'` to `INSTALLED_APPS` in `turkle/settings.py`
  - `python manage.py syncdb`
    Did not create user for django auth system
  - `python manage.py schemamigration hits --initial`

## TODO ##

*TBD*
