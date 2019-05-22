#!/usr/bin/env python

import argparse
from client import TurkleClient
import sys


parser = argparse.ArgumentParser(
    description="Downloads all the batches from Turkle",
    epilog="A batch must have at least one completed Task",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="protocol://hostname:port", default="http://localhost:8000")
parser.add_argument("--dir", help="directory to save files", default=".")
args = parser.parse_args()

client = TurkleClient(args.server, args.u, args.p)
result = client.download(args.dir)
if result:
    print("Success")
else:
    sys.exit(1)
