# CLI client

Το CLI υλοποιείται σε Python με χρήση argparse και εγκαθίσταται ως command-line εργαλείο με το όνομα se2534.

Δομή φακέλου 
cli-client/
│── main.py # Κύριο αρχείο CLI (argparse + API calls)
│── setup.py # Ρυθμίσεις εγκατάστασης CLI
│── requirements.txt # Εξαρτήσεις Python
│── testing.sh # Script για αυτοματοποιημένα tests με status code 200
│── testing2.sh # Script για αυτοματοποιημένα tests με λάθη εισόδου status codes 204 & 400
│── test.csv # Δοκιμαστικό CSV αρχείο για addpoints
│── README.md # Τεκμηρίωση CLI client

Προαπαιτούμενα
-Python 3.11+ 
-pip
-το API server τρέχει τοπικά (https://localhost:9876)
-σε Mac μπορεί να χρειαστεί (τοπικό) Python virtual environment 

Εγκατάσταση εξαρτήσεων για να δημιουργηθεί το command se2534
pip install -r requirements.txt

Χρήση του CLI
$ se2534 scope --param1 value1 [--param2 value2 ...] --format fff
Αν ο χρήστης δώσει scope που δεν υπάρχει, λανθασμένες παραμέτρους ή παραλείψει υποχρεωτικές παραμέτρους  εμφανίζεται υπόδειξη για τη σωστή σύνταξη της εντολής

Το αρχείο testing.sh περιέχει αυτοματοποιημένες κλήσεις του CLI για έλεγχο βασικής λειτουργικότητας.
Για να τρέξει:
chmod +x testing.sh
chmod +x testing2.sh
./testing.sh
./testing2.sh
