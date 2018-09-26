import argparse
from client import TurkleClient
import sys


parser = argparse.ArgumentParser()
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="hostname:port", default="localhost:8000")
parser.add_argument("username", help="new username")
parser.add_argument("password", help="new user's password")
args = parser.parse_args()

client = TurkleClient(args)
result = client.add_user()
if result:
    print("Success")
else:
    sys.exit(1)
