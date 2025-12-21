import argparse
import requests
import csv
import sys
import json


def convert_json_to_csv(data):
    # Παίρνει ένα dictionary (JSON) και το τυπώνει σε CSV μορφή.
    # Header = keys, Values = values
    writer = csv.writer(sys.stdout)
    writer.writerow(data.keys())
    writer.writerow(data.values())
    
def healthcheck(ar):

    url = 'https://localhost:9876/api/admin/healthcheck'

    response = requests.get(url)
    print(response.status_code)

    if response.status_code == 200:
      if ar.format.lower() == 'json':
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
      else:
        # print(response.text) #επιστρέφει κάπου csv ?
        convert_json_to_csv(response.text)
      return True

    # Σφάλμα (status ≠ 200)
    else:
        if ar.format.lower() == 'json':
          print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        else:
          convert_json_to_csv(response.text)

        return False


parser = argparse.ArgumentParser()
parser.add_argument(
    "--format",
    choices=["csv", "json"],
    default="csv",
    help="Choose format (default choice csv)"
)
args = parser.parse_args()

healthcheck(args)

