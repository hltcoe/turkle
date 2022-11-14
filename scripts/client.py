from bs4 import BeautifulSoup
import functools
import getpass
import os
import re
import requests


def exception_handler(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            if 'CERTIFICATE_VERIFY_FAILED' in str(e):
                print("Error: could not verify ssl certificate")
            else:
                print("Error: failed to contact site")
            return False
    return wrapper


class TurkleClient(object):
    LOGIN_URL = "/login/"
    ADD_USER_URL = "/admin/auth/user/add/"
    ADD_PROJECT_URL = "/admin/turkle/project/add/"
    ADD_BATCH_URL = "/admin/turkle/batch/add/"
    LIST_BATCH_URL = "/admin/turkle/batch/"
    AUTOCOMPLETE_URL = "/admin/autocomplete/"

    def __init__(self, server, admin, password=None):
        # prefix is for when the app is not run in the base of the web server
        if not password:
            self.password = getpass.getpass(prompt="Admin password: ")
        else:
            self.password = password
        self.admin = admin
        self.server = server.rstrip('/')

    @exception_handler
    def add_user(self, user, password, email=None):
        with requests.Session() as session:
            if not self.login(session):
                return False
            url = self.format_url(self.ADD_USER_URL)
            session.get(url)
            payload = {
                'username': user,
                'password1': password,
                'password2': password,
                'is_active': True,
                'csrfmiddlewaretoken': session.cookies['csrftoken'],
            }
            if email:
                payload['email'] = email
            session.headers.update({'referer': url})
            resp = session.post(url, data=payload)
            error = self.extract_error_message(resp)
            if error:
                print("Error: {}".format(error))
                return False
        return True

    @exception_handler
    def download(self, directory):
        with requests.Session() as session:
            if not self.login(session):
                return False
            url = self.format_url(self.LIST_BATCH_URL)
            resp = session.get(url)
            soup = BeautifulSoup(resp.text, features='html.parser')
            for row in soup.find('table', id='result_list').tbody.findAll('tr'):
                finished_col = row.find('td', {'class': 'field-assignments_completed'}).string
                download_link = row.find('td', {'class': 'field-download_csv'}).a
                if finished_col != '0':
                    resp = session.get(self.format_url(download_link['href']))
                    info = resp.headers['content-disposition']
                    filename = re.findall(r'filename="(.+)"', info)[0]
                    filename = os.path.join(directory, filename)
                    with open(filename, 'wb') as fh:
                        fh.write(resp.content)
        return True

    @exception_handler
    def upload(self, options):
        if not self.validate_upload(options):
            return False

        self.prepare_upload(options)

        with requests.Session() as session:
            if not self.login(session):
                return False
            if not self.upload_project(session, options):
                return False
            review_url = self.upload_csv(session, options)
            if not review_url:
                return False
            return self.review_batch(session, review_url)

    def upload_project(self, session, options):
        url = self.format_url(self.ADD_PROJECT_URL)
        session.get(url)
        payload = {
            'name': options.project_name,
            'assignments_per_task': options.num,
            'filename': options.template,
            'html_template': options.form,
            'active': 1,
            'csrfmiddlewaretoken': session.cookies['csrftoken'],
        }
        if options.login:
            payload['login_required'] = 1
        session.headers.update({'referer': url})
        resp = session.post(url, data=payload)
        if resp.status_code != requests.codes.ok:
            print("Error: uploading the project failed")
            return False
        return True

    def upload_csv(self, session, options):
        project_id = self.get_autocomplete_id(session, options.project_name, 'batch', 'project')
        if not project_id:
            print("Error: unable to create the batch of tasks due to project ID failure")
            return None
        url = self.format_url(self.ADD_BATCH_URL)
        session.get(url)
        payload = {
            'project': project_id,
            'name': options.batch_name,
            'assignments_per_task': options.num,
            'active': 1,
            'csrfmiddlewaretoken': session.cookies['csrftoken'],
        }
        if options.login:
            payload['login_required'] = 1
        files = {'csv_file': (options.csv, options.csv_data)}
        session.headers.update({'referer': url})
        resp = session.post(url, data=payload, files=files)
        if resp.status_code != requests.codes.ok:
            print("Error: uploading the csv failed")
            return None
        if b'correct the error' in resp.content:
            print("Error: the csv file is invalid. Try uploading using the admin UI.")
            return None
        return resp.url

    def get_autocomplete_id(self, session, term, model_name, field_name):
        url = self.format_url(self.AUTOCOMPLETE_URL)
        resp = session.get(url, params={
            'term': term,
            'app_label': 'turkle',
            'model_name': model_name,
            'field_name': field_name,
        })
        if resp.status_code != requests.codes.ok or not resp.json()['results']:
            return None
        return resp.json()['results'][0]['id']

    def review_batch(self, session, url):
        url = url.replace('review', 'publish')
        payload = {
            'csrfmiddlewaretoken': session.cookies['csrftoken'],
        }
        resp = session.post(url, data=payload)
        if resp.status_code != requests.codes.ok:
            print("Error: publishing batch failed")
            return False
        return True

    def validate_upload(self, options):
        # tasks that don't require a log in can only be done once
        if not options.login and options.num != 1:
            print("Error: login cannot be off if more than 1 assignment per task")
            return False

        if not os.path.exists(options.template):
            print("Error: template path does not exist")
            return False

        if not os.path.exists(options.csv):
            print("Error: csv path does not exist")
            return False

        return True

    def prepare_upload(self, options):
        if not options.project_name:
            options.project_name = self.extract_name(options.template)
        if not options.batch_name:
            options.batch_name = self.extract_name(options.csv)
        options.form = self.read_file(options.template)
        options.template = os.path.basename(options.template)
        options.csv_data = self.read_file(options.csv)
        options.csv = os.path.basename(options.csv)

    @staticmethod
    def read_file(filename):
        with open(filename, "r") as fh:
            data = fh.read()
            return data

    @staticmethod
    def extract_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    @staticmethod
    def extract_error_message(resp):
        # returns None if no error message
        soup = BeautifulSoup(resp.text, features='html.parser')
        if soup.find('p', class_='errornote'):
            for error in soup.find('ul', class_='errorlist'):
                return error.string

    def login(self, session):
        result = True
        url = self.format_url(self.LOGIN_URL)
        session.get(url)
        payload = {
            'username': self.admin,
            'password': self.password,
            'csrfmiddlewaretoken': session.cookies['csrftoken'],
        }
        session.headers.update({'referer': url})
        resp = session.post(url, data=payload)
        if "didn't match" in resp.text or 'Admin' not in resp.text:
            # catching user/pass failures and account not having admin
            print("Error: login failure")
            result = False
        return result

    def format_url(self, path):
        return self.server + path
