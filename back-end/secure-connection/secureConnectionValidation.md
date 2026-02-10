# 🛠️ Short Guide: How to check if connections are secure
## Install relevant packages if not already installed
pip install cryptography

## If cert.pem and key.pem files haven't been generated, run
python generateCertificates.py

## ⚠️ Move the cert.pem and key.pem files in the same path as main
## Run on local host
uvicorn main:app --host 0.0.0.0 --port 9876 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload

## All addresses should be in https on the Swagger FastAPI interface
https://0.0.0.0:9876

## Run the following script for automated tests while local host is up and running
python secureConnectionTestingScript.py