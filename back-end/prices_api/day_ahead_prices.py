import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
import csv
from pathlib import Path
import os                      
from dotenv import load_dotenv  

load_dotenv()                   

# Settings
EIC_GR = "10YGR-HTSO-----Y"
BASE_URL = "https://web-api.tp.entsoe.eu/api"
TZ_ATHENS = ZoneInfo("Europe/Athens")

# --- TOKEN HERE ---
SECURITY_TOKEN = os.getenv("ENTSOE_TOKEN") 

def build_url(token, start_utc, end_utc):
    fmt = "%Y%m%d%H%M"
    return (
        f"{BASE_URL}?securityToken={token}&documentType=A44"
        f"&in_Domain={EIC_GR}&out_Domain={EIC_GR}"
        f"&periodStart={start_utc.strftime(fmt)}&periodEnd={end_utc.strftime(fmt)}"
    )

def fetch_xml(url):
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def parse_data(xml_text):
    if not xml_text: return []
    ns = {"ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"}
    
    try:
        root = ET.fromstring(xml_text)
    except:
        return []

    results = []
    for ts in root.findall(".//ns:TimeSeries", ns):
        period = ts.find("ns:Period", ns)
        if period is None: continue

        start_str = period.findtext("ns:timeInterval/ns:start", namespaces=ns)
        res_str = period.findtext("ns:resolution", namespaces=ns)
        
        if not start_str or not res_str: continue

        start_utc = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(timezone.utc)
        step = 15 if res_str == "PT15M" else (60 if res_str == "PT60M" else 0)
        
        if step == 0: continue

        for p in period.findall("ns:Point", ns):
            pos = int(p.findtext("ns:position", namespaces=ns))
            price_mwh = float(p.findtext("ns:price.amount", namespaces=ns))
            
            # ΜΕΤΑΤΡΟΠΗ: Από MWh σε kWh (Διαίρεση με 1000)
            price_kwh = price_mwh / 1000.0
            
            point_utc = start_utc + timedelta(minutes=step * (pos - 1))
            point_athens = point_utc.astimezone(TZ_ATHENS)
            results.append((point_athens, price_kwh))

    return results

def aggregate_to_hourly(points):
    """
    points: list of (datetime_athens, price_kwh) possibly at 15-min.
    returns: list of (datetime_athens_hour, price_kwh_hour)
    """
    buckets = {}
    for dt, price in points:
        hour_dt = dt.replace(minute=0, second=0, microsecond=0)
        buckets.setdefault(hour_dt, []).append(price)
    hourly = []
    for h in sorted(buckets.keys()):
        vals = buckets[h]
        hourly.append((h, sum(vals) / len(vals)))  # average
    return hourly


def main():
    if not SECURITY_TOKEN:
        print("Error: Token is missing.")
        return

    # Target tomorrow (00:00 - 00:00 local time)
    target_date = date.today() + timedelta(days=1)
    start_local = datetime(target_date.year, target_date.month, target_date.day, 0, 0, tzinfo=TZ_ATHENS)
    end_local = start_local + timedelta(days=1)

    # Request wider range (UTC buffer)
    utc_req_start = (start_local - timedelta(days=1)).astimezone(timezone.utc)
    utc_req_end = (end_local + timedelta(days=1)).astimezone(timezone.utc)

    url = build_url(SECURITY_TOKEN, utc_req_start, utc_req_end)
    xml_data = fetch_xml(url)
    all_data = parse_data(xml_data)

    # Filter for the Greek 24-hour period
    final_data = [x for x in all_data if start_local <= x[0] < end_local]
    final_data.sort(key=lambda x: x[0])
    final_data = aggregate_to_hourly(final_data)

    if not final_data:
        print("No data found for target date.")
        return

    # Static filename to ensure overwrite
    out_path = Path(__file__).parent / "prices.csv"
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        # Header changed to eur_per_kwh
        w.writerow(["datetime_athens", "eur_per_kwh"])
        for dt, price in final_data:
            # Format with 5 decimal places for precision (e.g. 0.12345)
            w.writerow([dt.strftime('%Y-%m-%d %H:%M'), f"{price:.5f}"])

    print(f"File saved: {out_path}")

if __name__ == "__main__":
    main()