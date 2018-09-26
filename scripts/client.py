import functools
import getpass
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
            session.post(url, data=payload)
        return True

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
