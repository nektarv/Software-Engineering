import argparse
import requests
import json
import csv
import sys
import os 
from io import StringIO
from datetime import datetime
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def normalize_date(date_str: str) -> str:
    """
    Δέχεται ημερομηνία σε format:
      YYYYMMDD, YYYY-MM-DD ή YYYY/MM/DD
    και επιστρέφει string YYYYMMDD για το API.
    """
    # Καθαρίζουμε διαχωριστικά
    cleaned = date_str.replace("-", "").replace("/", "")

    # Τώρα πρέπει να είναι 8 χαρακτήρες
    if len(cleaned) != 8 or not cleaned.isdigit():
        raise ValueError(f"Invalid date format: {date_str}. Expected YYYYMMDD, YYYY-MM-DD, or YYYY/MM/DD")

    # Ελέγχουμε αν είναι έγκυρη ημερομηνία
    try:
        dt = datetime.strptime(cleaned, "%Y%m%d")
        return dt.strftime("%Y%m%d")
    except ValueError:
        raise ValueError(f"Invalid date: {date_str}")


# -------------------------------
# Healthcheck
# -------------------------------
def healthcheck():

    url = 'https://localhost:9876/api/admin/healthcheck' 
    response = requests.get(url,verify=False)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# -------------------------------
# Resetpoints
# -------------------------------
def resetpoints():

    url = 'https://localhost:9876/api/admin/resetpoints'
    response = requests.post(url,verify=False)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# -------------------------------
# Addpoints
# -------------------------------
def addpoints(source):

    url = 'https://localhost:9876/api/admin/addpoints'

    if not os.path.exists(source):
        print(f"The file {source} was not found.")
        sys.exit(1)

    with open(source, "rb") as f:
        # (όνομα αρχείου, περιεχόμενο, MIME type)
        files = {"file": (os.path.basename(source), f, "text/csv")}
        response = requests.post(url, files=files, verify=False)
    print(response.status_code)
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

# -------------------------------
#   Points
# -------------------------------
def points(status=None, output_format="csv"):

    url = 'https://localhost:9876/api/points' 

    params = {}
    if status:
        params["status"] = status
    if output_format:
        params["format"] = output_format.lower()  # csv ή json

    response = requests.get(url, params=params, verify=False)
    print(response.status_code)

    if response.status_code >= 400:
        error_log = response.json()
        print(json.dumps(error_log, ensure_ascii=False, indent=2))
        return

    if response.status_code == 204:
        print("No data found")
        return

    if output_format.lower() == "json":
        data = response.json()
        data_sorted = sorted(data, key=lambda x: int(x["pointid"]))
        print(json.dumps(data_sorted, ensure_ascii=False, indent=2))
    else:
        # CSV
        csv_text = response.text
        reader = csv.DictReader(StringIO(csv_text))
        data = list(reader)
        data_sorted = sorted(data, key=lambda x: int(x["pointid"]))
        writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
        writer.writeheader()
        writer.writerows(data_sorted)


# -------------------------------
#   Point
# -------------------------------
def point(point_id: int):
 
    url = f"https://localhost:9876/api/point/{point_id}"       
    response = requests.get(url, verify=False)
    print(response.status_code)
    if response.status_code == 204:
        print("No data found")
        return
    else:
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))

# -------------------------------
#   Reserve
# -------------------------------
def reserve(point_id: int, minutes: int = None):
    if minutes is None:
        url = f"https://localhost:9876/api/reserve/{point_id}"
    else:
        url = f"https://localhost:9876/api/reserve/{point_id}/{minutes}"
    
    response = requests.post(url, verify=False)
    print(response.status_code)
    if response.status_code == 204:
        print("No data found")
        return
    else:
        data = response.json()
        print(json.dumps(data, ensure_ascii=False, indent=2))   

# -------------------------------
#   Updpoint
# -------------------------------
def updpoint(point_id: int, status: str = None, price: float = None):
    if status is None and price is None:
        raise ValueError("At least one of --status or --price must be provided")
    
    payload = {}
    if status:
        payload["status"] = status
    if price:
        payload["kwhprice"] = price
    
    url=f"https://localhost:9876/api/updpoint/{point_id}"
    response = requests.post(url, json=payload, verify=False)
    print(response.status_code)
    if response.status_code == 204:
        print("No data found")
        return
    else:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))

# -------------------------------
#   Newsession
# -------------------------------
def newsession(pointid: int, starttime: str, endtime: str, startsoc: int,
               endsoc: int, totalkwh: float, kwhprice: float, amount: float):
    payload = {
        "pointid": pointid,
        "starttime": starttime,
        "endtime": endtime,
        "startsoc": startsoc,
        "endsoc": endsoc,
        "totalkwh": totalkwh,
        "kwhprice": kwhprice,
        "amount": amount
    }
    url= "https://localhost:9876/api/newsession"
    response = requests.post(url, json=payload,verify=False)
    print(response.status_code) 
    if response.status_code == 204:
        print("No data found")
        return
    else:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
 
# -------------------------------
#   Sessions 
# -------------------------------
def sessions(pointid, from_date, to_date, output_format="csv"):

    dt_from_str = normalize_date(from_date)
    dt_to_str = normalize_date(to_date)
    url = f"https://localhost:9876/api/sessions/{pointid}/{dt_from_str}/{dt_to_str}?format={output_format}"
    response = requests.get(url, verify=False)
    print(response.status_code)

    if response.status_code >= 400:
        error_log = response.json()
        print(json.dumps(error_log, ensure_ascii=False, indent=2))
        return

    if response.status_code == 204:
        # Κενά δεδομένα 
        print("No sessions found.")
        return
    else:
        if output_format.lower() == "json":
            data = response.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            # CSV
            csv_text = response.text
            reader = csv.DictReader(StringIO(csv_text))
            data = list(reader)
            writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(data)


# -------------------------------
#   Pointstatus 
# -------------------------------
def pointstatus(id, from_date, to_date, output_format="csv"):

    dt_from_str = normalize_date(from_date)
    dt_to_str = normalize_date(to_date)
    url = f"https://localhost:9876/api/pointstatus/{id}/{dt_from_str}/{dt_to_str}?format={output_format}"
    
    response = requests.get(url, verify=False)
    print(response.status_code)

    if response.status_code >= 400:
        error_log = response.json()
        print(json.dumps(error_log, ensure_ascii=False, indent=2))
        return
    
    if response.status_code == 204:
        print( "No point status changes found.")
        return
    else:
        if output_format.lower() == "json":
            data = response.json()
            #print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            # CSV
            csv_text = response.text
            reader = csv.DictReader(StringIO(csv_text))
            data = list(reader)
            #writer = csv.DictWriter(sys.stdout, fieldnames=reader.fieldnames)
            #writer.writeheader()
            #writer.writerows(data)

        if data and "timeref" in data[0]:
            data.sort(key=lambda x: x["timeref"], reverse=True)

        if output_format.lower() == "json":
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            writer = csv.DictWriter(sys.stdout, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)

def main():
    parser = argparse.ArgumentParser(description="CLI για EV Charging API")
    subparsers = parser.add_subparsers(dest="scope", required=True)
    #healthcheck
    subparsers.add_parser("healthcheck", help="Έλεγχος σύνδεσης")
    #resetpoints
    subparsers.add_parser("resetpoints", help="Αρχικοποίηση σημείων φόρτισης")
    #addpoints
    p_add = subparsers.add_parser("addpoints", help="Προσθήκη σημείων από csv")
    p_add.add_argument(
        "--source", 
        required=True,       # υποχρεωτικό
        help="Όνομα CSV αρχείου με δεδομένα νέων σημείων"
    )
    #points
    p_points = subparsers.add_parser("points", help="Λίστα σημείων φόρτισης")
    p_points.add_argument("--status", type=str, choices=["available","charging","reserved","offline","malfunction"],
                          help="Φιλτράρισμα κατά status")
    p_points.add_argument("--format", type=str, choices=["csv","json"], default="csv",
                          help="Μορφότυπος εξόδου")
    #point
    p_point = subparsers.add_parser("point", help="Πληροφορίες συγκεκριμένου σημείου")
    p_point.add_argument("--id", required=True, help="ID σημείου φόρτισης")

    #reserve
    p_reserve = subparsers.add_parser("reserve", help="Κράτηση σημείου φόρτισης")
    p_reserve.add_argument("--id", required=True, help="ID σημείου φόρτισης")
    p_reserve.add_argument("--minutes", type=int, help="Διάρκεια κράτησης σε λεπτά")

    #updpoint
    p_upd = subparsers.add_parser("updpoint", help="Ενημέρωση σημείου φόρτισης")
    p_upd.add_argument("--id", required=True, help="ID σημείου φόρτισης")
    p_upd.add_argument("--status", type=str, choices=["available","charging","reserved","offline","malfunction"],
                      help="Νέο status")
    p_upd.add_argument("--price", type=float, help="Νέα τιμή ανά kWh")

    #newsession
    p_newsess = subparsers.add_parser("newsession", help="Καταγραφή γεγονότος φόρτισης")
    p_newsess.add_argument("--id", required=True, help="ID σημείου φόρτισης")
    p_newsess.add_argument("--starttime", required=True, help="Χρόνος έναρξης")
    p_newsess.add_argument("--endtime", required=True, help="Χρόνος λήξης")
    p_newsess.add_argument("--startsoc", type=int, required=True, help="SOC έναρξης (%)")
    p_newsess.add_argument("--endsoc", type=int, required=True, help="SOC λήξης (%)")
    p_newsess.add_argument("--totalkwh", type=float, required=True, help="Συνολικά kWh")
    p_newsess.add_argument("--kwhprice", type=float, required=True, help="Τιμή ανά kWh")
    p_newsess.add_argument("--amount", type=float, required=True, help="Συνολικό ποσό")

    #sessions
    p_sess = subparsers.add_parser("sessions", help="Λίστα γεγονότων φόρτισης")
    p_sess.add_argument("--id", required=True, help="ID σημείου φόρτισης")
    p_sess.add_argument("--from", required=True, dest="from_date", help="Ημερομηνία από")
    p_sess.add_argument("--to", required=True, dest="to_date", help="Ημερομηνία έως")
    p_sess.add_argument("--format", type=str, choices=["csv","json"], default="csv",
                       help="Μορφότυπος εξόδου")

    #pointstatus
    p_status = subparsers.add_parser("pointstatus", help="Λίστα συνεδριών")
    p_status.add_argument("--id", required=True, help="ID σημείου φόρτισης")
    p_status.add_argument("--from", required=True, dest="from_date", help="Ημερομηνία από")
    p_status.add_argument("--to", required=True, dest="to_date", help="Ημερομηνία έως")
    p_status.add_argument("--format", type=str, choices=["csv","json"], default="csv",
                       help="Μορφότυπος εξόδου")

    args = parser.parse_args()

    if args.scope == "healthcheck":
        healthcheck()
    elif args.scope == "resetpoints":
        resetpoints()
    elif args.scope == "addpoints":
        addpoints(args.source)
    elif args.scope == "points":
        points(args.status, args.format)
    elif args.scope == "point":
        point(args.id)
    elif args.scope == "reserve":
        reserve(args.id, args.minutes)
    elif args.scope == "updpoint":
        # Έλεγχος ότι τουλάχιστον ένα από status/price έχει δοθεί
        if args.status is None and args.price is None:
            parser.error("--updpoint requires at least one of --status or --price")
            sys.exit(1)
        updpoint(args.id, args.status, args.price)
    elif args.scope == "newsession":
        newsession(args.id, args.starttime, args.endtime, args.startsoc, 
                  args.endsoc, args.totalkwh, args.kwhprice, args.amount)
    elif args.scope == "sessions":
        sessions(args.id, args.from_date, args.to_date, args.format)
    elif args.scope == "pointstatus":
        pointstatus(args.id, args.from_date, args.to_date, args.format)
 
