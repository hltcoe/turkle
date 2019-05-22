#!/usr/bin/env python

import argparse
from client import TurkleClient
import sys


parser = argparse.ArgumentParser(
    description="Add a user to Turkle",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="protocol://hostname:port", default="http://localhost:8000")
parser.add_argument("--email", help="new user's email address")
parser.add_argument("username", help="new username")
parser.add_argument("password", help="new user's password")
args = parser.parse_args()

client = TurkleClient(args.server, args.u, args.p)
result = client.add_user(args.username, args.password, args.email)
if result:
    print("Success")
else:
    sys.exit(1)
