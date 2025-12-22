import requests
import json

def healthcheck(ar):

    url = 'https://localhost:9876/api/admin/healthcheck'

    response = requests.get(url)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

healthcheck() 

