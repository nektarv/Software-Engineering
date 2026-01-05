# To check for https connection:
## Install relevant packages if not already installed
pip install cryptography

## If cert.pem and key.pem files are present, this should be optional
python generate_certs.py

## Run local host
uvicorn main:app --host 0.0.0.0 --port 9876 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload

You should see all links in https on Swagger FastAPI

### Run script for automated tests while local host is up and running
python https_test.py