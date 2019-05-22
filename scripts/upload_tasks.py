#!/usr/bin/env python

import argparse
from client import TurkleClient
import sys


parser = argparse.ArgumentParser(
    description="Upload a batch of tasks to Turkle",
    epilog="Requires a template and the batch CSV",
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("-u", help="admin username", required=True)
parser.add_argument("-p", help="admin password")
parser.add_argument("--server", help="protocol://hostname:port", default="http://localhost:8000")
parser.add_argument("--num", help="number of assignments per task", default=1, type=int)
parser.add_argument("--login", help="is login required (0 or 1)",
                    default=1, type=int, choices=[0, 1])
parser.add_argument("--project-name", help="Name of the project")
parser.add_argument("--batch-name", help="Name of the batch")
parser.add_argument("template", help="html template file")
parser.add_argument("csv", help="csv file for batch")
args = parser.parse_args()

client = TurkleClient(args.server, args.u, args.p)
result = client.upload(args)
if result:
    print("Success")
else:
    sys.exit(1)
