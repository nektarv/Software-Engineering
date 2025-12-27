
import argparse
import requests
import json
import sys
import os

# πριν τρεξω κάποιο command $ se25XX scope --param1 value1 [--param2 value2 ...] --format fff τρέχω pip install -e .

# -------------------------------
# Healthcheck
# -------------------------------
def healthcheck():

    url = 'http://localhost:9876/api/admin/healthcheck' # σωστό link url = 'https://localhost:9876/api/admin/healthcheck'
    response = requests.get(url)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# -------------------------------
# Resetpoints
# -------------------------------
def resetpoints():

    url = 'http://localhost:9876/api/admin/resetpoints'
    response = requests.post(url)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# -------------------------------
# Addpoints
# -------------------------------
def addpoints(source):

    url = 'http://localhost:9876/api/admin/addpoints'

    if not os.path.exists(source):
        print(f"Το αρχείο {source} δεν βρέθηκε.")
        sys.exit(1)

    with open(source, "rb") as f:
        # (όνομα αρχείου, περιεχόμενο, MIME type)
        files = {"file": (os.path.basename(source), f, "text/csv")}
        response = requests.post(url, files=files)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description="CLI για EV Charging API")
    subparsers = parser.add_subparsers(dest="scope", required=True)

    subparsers.add_parser("healthcheck", help="Έλεγχος σύνδεσης")

    subparsers.add_parser("resetpoints", help="Αρχικοποίηση σημείων φόρτισης")

    parser_add = subparsers.add_parser("addpoints", help="Προσθήκη σημείων από csv")
    parser_add.add_argument(
        "--source", 
        required=True,       # υποχρεωτικό
        help="Όνομα CSV αρχείου με δεδομένα νέων σημείων"
    )

    args = parser.parse_args()

    if args.scope == "healthcheck":
        healthcheck()
    elif args.scope == "resetpoints":
        resetpoints()
    elif args.scope == "addpoints":
        addpoints(args.source)

