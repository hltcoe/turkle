from bs4 import BeautifulSoup
import functools
import getpass
import os
import re
import requests


def exception_handler(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except requests.exceptions.ConnectionError:
            print("Error: failed to contact site")
            return False
    return wrapper


class TurkleClient(object):
    LOGIN_URL = "/login/"
    ADD_USER_URL = "/admin/auth/user/add/"
    ADD_TEMPLATE_URL = "/admin/hits/hittemplate/add/"
    ADD_BATCH_URL = "/admin/hits/hitbatch/add/"
    LIST_BATCH_URL = "/admin/hits/hitbatch/"

    def __init__(self, args):
        if not args.p:
            args.p = getpass.getpass(prompt="Admin password: ")
        self.args = args

    @exception_handler
    def add_user(self):
        with requests.Session() as session:
            if not self.login(session):
                return False
            url = self.format_url(self.ADD_USER_URL)
            session.get(url)
            payload = {
                'username': self.args.username,
                'password1': self.args.password,
                'password2': self.args.password,
                'csrfmiddlewaretoken': session.cookies['csrftoken']
            }
            resp = session.post(url, data=payload)
            if "username already exists" in resp.text:
                print("Error: username already exists")
                return False
        return True

    @exception_handler
    def download(self):
        with requests.Session() as session:
            if not self.login(session):
                return False
            url = self.format_url(self.LIST_BATCH_URL)
            resp = session.get(url)
            soup = BeautifulSoup(resp.text, features='html.parser')
            for row in soup.find('table', id='result_list').tbody.findAll('tr'):
                finished_col = row.find('td', {'class': 'field-total_finished_hits'}).string
                download_col = row.findAll('td')[-1].a
                if finished_col != '0':
                    resp = session.get(self.format_url(download_col['href']))
                    info = resp.headers['content-disposition']
                    filename = re.findall(r'filename="(.+)"', info)[0]
                    filename = os.path.join(self.args.dir, filename)
                    with open(filename, 'wb') as fh:
                        fh.write(resp.content)
        return True

    @exception_handler
    def publish(self):
        if not self.validate_publish():
            return False

        self.prepare_publish()

        with requests.Session() as session:
            if not self.login(session):
                return False
            if not self.upload_template(session):
                return False
            return self.upload_csv(session)

    def upload_template(self, session):
        url = self.format_url(self.ADD_TEMPLATE_URL)
        session.get(url)
        payload = {
            'name': self.args.template_name,
            'assignments_per_hit': self.args.num,
            'filename': self.args.template,
            'form': self.args.form,
            'active': 1,
            'csrfmiddlewaretoken': session.cookies['csrftoken']
        }
        if self.args.login:
            payload['login_required'] = 1
        resp = session.post(url, data=payload)
        if resp.status_code != requests.codes.ok:
            print("Error: uploading the template failed")
            return False
        return True

    def upload_csv(self, session):
        url = self.format_url(self.ADD_BATCH_URL)
        resp = session.get(url)
        # grab a list of the template ids from the form
        regex = r'<option value="(.*)">'
        ids = re.findall(regex, resp.text)
        payload = {
            # we just upload a template so we assume that its last in list
            'hit_template': ids[-1],
            'name': self.args.batch_name,
            'assignments_per_hit': self.args.num,
            'active': 1,
            'csrfmiddlewaretoken': session.cookies['csrftoken']
        }
        files = {'csv_file': (self.args.csv, self.args.csv_data)}
        resp = session.post(url, data=payload, files=files)
        if resp.status_code != requests.codes.ok:
            print("Error: uploading the csv failed")
            return False
        return True

    def validate_publish(self):
        # HITs that don't require a log in can only be done once
        if not self.args.login and self.args.num != 1:
            print("Error: login cannot be off if more than 1 assignment per hit")
            return False

        if not os.path.exists(self.args.template):
            print("Error: template path does not exist")
            return False

        if not os.path.exists(self.args.csv):
            print("Error: csv path does not exist")
            return False

        return True

    def prepare_publish(self):
        if not self.args.template_name:
            self.args.template_name = self.extract_name(self.args.template)
        if not self.args.batch_name:
            self.args.batch_name = self.extract_name(self.args.csv)
        self.args.form = self.read_file(self.args.template)
        self.args.template = os.path.basename(self.args.template)
        self.args.csv_data = self.read_file(self.args.csv)
        self.args.csv = os.path.basename(self.args.csv)

    @staticmethod
    def read_file(filename):
        with open(filename, "r") as fh:
            data = fh.read()
            return data

    @staticmethod
    def extract_name(filename):
        return os.path.splitext(os.path.basename(filename))[0]

    def login(self, session):
        result = True
        url = self.format_url(self.LOGIN_URL)
        session.get(url)
        payload = {
            'username': self.args.u,
            'password': self.args.p,
            'csrfmiddlewaretoken': session.cookies['csrftoken']
        }
        resp = session.post(url, data=payload)
        if "didn't match" in resp.text:
            print("Error: login failure")
            result = False
        return result

    def format_url(self, path):
        return "http://" + self.args.server + path
