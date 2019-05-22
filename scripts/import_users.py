#!/usr/bin/env python

import argparse
from client import TurkleClient
import csv
import sys


parser = argparse.ArgumentParser(
    description="Import a list of users from a CSV",
    epilog="The CSV should have no header with format: username,password,email[optional]",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="protocol://hostname:port", default="http://localhost:8000")
parser.add_argument("csv", help="csv filename")
args = parser.parse_args()

client = TurkleClient(args.server, args.u, args.p)
with open(args.csv, 'r') as fh:
    reader = csv.reader(fh)
    result = True
    count = 0
    for row in reader:
        if len(row) == 2:
            result |= client.add_user(row[0].strip(), row[1].strip())
        else:
            result |= client.add_user(row[0].strip(), row[1].strip(), row[2].strip())
        if not result:
            break
        count += 1
    if result:
        print("Added {} users".format(count))
    else:
        sys.exit(1)
