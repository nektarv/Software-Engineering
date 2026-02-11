# ⚡ ElectroWay
ElectroWay is a university Software Engineering project developed for the **Software Engineering** course, at the **School of Electrical and Computer Engineering, NTUA**.

## 📌 Project Description
The goal of this project was to design and implement software for a provider of EV charging stations.
This repository contains the source code, documentation, and artifacts produced during the project.

## 🧭 Run the Software - A short guide
On a terminal, navigate to .../softeng25-34/back-end and run the following command:

uvicorn main:app --host 0.0.0.0 --port 9876 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload

On a separate terminal, navigate to .../softeng25-34/front-end and run the following command:

uvicorn app:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload

You may access the app at:
https://localhost:8000 or https://0.0.0.0:8000

## 📋 Project Management
We used Github Projects to organize our work - https://github.com/orgs/ntua/projects/298

## 📁 Project Structure

### /back-end
- API endpoints (/endpoints and /management)
- additional endpoints for backend operations

### /cli-client
- CLI implementation
- CLI testing script (/cli-client)

### /database
- database structure
- dummy data
- ER diagram

### /documentation
- SRS doc and VP diagrams from first phase
- SRS doc and VP diagrams from second phase
- API documentation

### /front-end
- all relevant files (.html, .css, .js) for frontend implementation

### /test
- API testing script