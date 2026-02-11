# Back-end

**Indicative contents:**

* Core RESTful API source code.
* Administrative management modules for CLI.
* Real-time energy pricing subsystem.
* SSL/TLS security assets.
* Dependencies and verification utilities.

Για να τρέξει το backend, αφού πλοηγηθούμε στο κατάλληλο path .../back-end μέσω τερματικού, εκτελούμε:
uvicorn main:app --host 0.0.0.0 --port 9876 --ssl-keyfile key.pem --ssl-certfile cert.pem --reload

Μπορούμε στη συνέχεια να πλοηγηθούμε στο https://127.0.0.1:9876/ ή στο https://localhost:9876/docs#/