import argparse
import requests
import json

def healthcheck(ar):

    url = 'https://localhost:9876/api/admin/healthcheck'

    response = requests.get(url)
    print(response.status_code)

    if response.status_code == 200:
      if ar.format.lower() == 'json':
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
      return True

    # Σφάλμα (status ≠ 200)
    else:
        if ar.format.lower() == 'json':
          print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        return False


parser = argparse.ArgumentParser()
parser.add_argument(
    "--format",
    choices=["json"],
    default="json",
    help="Only json format is provided"
)
args = parser.parse_args()

healthcheck(args)

