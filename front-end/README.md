# Front-end

**Indicative contents:**

* Application source code for user interface management and API communication.
* Dynamic page rendering templates (UI Templates).
* Styling and formatting files (CSS).
* Security certificates (SSL/TLS).
* Environment dependency management files.

Υλοποιήθηκαν 5 βασικές οθόνες σε browser: χάρτης, τιμοκατάλογος, στατιστικά, login και register. 
Η οθόνη τών στατιστικών μπορει να προσαρμόσει το frontend της σε οθόνη κινητού. 

Για τη σωστή λειτουργία των templates απαιτείται η βιβλιοθήκη **jinja2**: pip install jinja2 και οι βιβλιοθήκες του API

Για να τρέξει το frontend, αφού στο back-end τρέχει το API, εκτελείται η παρακάτω εντολή:
uvicorn app:app --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload
Η εφαρμογή είναι προσβάσιμη στη διεύθυνση: https://localhost:8000 ή https://0.0.0.0:8000
Ο browser ενδέχεται να εμφανίσει προειδοποίηση ασφαλείας λόγω self-signed certificate.

Έλεγχος οθόνης στατιστικών σε Emulator Κινητής Συσκευής μέσω του Safari:
Ανοίγουμε σε ένα παράθυρο του Safari την εφαρμογή -> Επιλέγουμε Ανάπτυξη από τo μενού -> Είσοδος σε λειτουργία αποκριτικής ιστοσχεδίασης 
-> επιλέγουμε προσαρμοσμένο μέγεθος 