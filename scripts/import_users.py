import argparse
from client import TurkleClient
import csv
import sys


parser = argparse.ArgumentParser(
    description="Import a list of users from a CSV",
    epilog="The CSV should have no header with format: username,password"
)
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="hostname:port", default="localhost:8000")
parser.add_argument("csv", help="csv filename")
args = parser.parse_args()

client = TurkleClient(args)
with open(args.csv, 'r') as fh:
    reader = csv.reader(fh)
    result = True
    count = 0
    for row in reader:
        result |= client.add_user(row[0].strip(), row[1].strip())
        if not result:
            break
        count += 1
    if result:
        print("Added {} users".format(count))
    else:
        sys.exit(1)
