Turkle Commandline Scripts
---------------------------

These scripts provide access to commonly performed tasks that can be automated such as
adding worker accounts, uploading new annotation tasks, and downloading results.

Installing
============
These scripts are python3 only and depend on requests and BeautifulSoup.
They do not depend on the Turkle code.

Usage
============
Because Turkle does not have a RESTful API currently, the scripts log in
to the Turkle site, fill out forms, and submit them. Besides the individual
parameters for each script, they require the username of the admin account,
the password for that account (which they will ask for if not provided), and
the URL for the site. If the Turkle site is not available on port 80 (http) or
port 443 (https), the port has to be included in the URL. Otherwise, it can
be left off. If Turkle is not running in the root of the web server, that 
path has to be included in the URL.

Example of adding a user:
```bash
python add_user.py -u admin --server https://turkle.com new_user new_password 
```
