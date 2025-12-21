import json
from pathlib import Path
import mysql.connector
from management.utils import DB_CONFIG  

CONNECTOR_MAP = {
    2: "J-1772", 3: "CHAdeMO", 7: "Type 2", 8: "Type 3A", 10: "Wall (Euro)",
    13: "CCS1", 14: "Three Phase EU", 15: "Caravan Mains Socket", 20: "CCS2", 24: "Type 3A",
}

def map_status(status: str) -> str:
    if status == "AVAILABLE": return "available"
    if status == "CHARGING": return "charging"
    if status in ("OUTOFORDER", "UNDERREPAIR"): return "malfunction"
    return "offline"

def round_decimal(value, decimals: int):
    if value is None: return 0.0
    factor = 10 ** decimals
    return int(round(float(value) * factor)) / factor

def insert_from_json(conn, cursor, json_path: Path, max_locations: int = 10):
    """Εισάγει δεδομένα από JSON -> DB"""
    with json_path.open("r", encoding="utf-8") as f:
        locations = json.load(f)

    inserted_stations = 0
    for idx, loc in enumerate(locations):
        if idx >= max_locations: break

        # Station INSERT
        cursor.execute("""
            INSERT INTO station (address, Latitude, Longitude, name, provider) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            loc.get("address"),
            round_decimal(loc.get("latitude"), 4),
            round_decimal(loc.get("longitude"), 4),
            loc.get("name"), 
            "ElectroWay"
        ))
        
        station_id = cursor.lastrowid
        inserted_stations += 1

        # Outlets INSERT
        is_fast = 1 if loc.get("is_fast_charger") else 0
        for st in loc.get("stations", []):
            for out in st.get("outlets", []):
                connector = CONNECTOR_MAP.get(out.get("connector"), f"connector{out.get('connector')}")
                power = int(round(out.get("kilowatts", 0)))
                state = map_status(out.get("status"))
                
                cursor.execute("""
                    INSERT INTO outlet (stationid, connector, power, state, is_fast, markup) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (station_id, connector, power, state, is_fast, 1.0))
    
    conn.commit()
    return inserted_stations
