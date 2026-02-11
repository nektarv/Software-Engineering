import json
from pathlib import Path
import mysql.connector
import random
from decimal import Decimal, ROUND_HALF_UP

def random_markup(min_val=1.05, max_val=1.30):
    value = Decimal(str(random.uniform(min_val, max_val)))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

CONNECTOR_MAP = {
    2: "J-1772", 3: "CHAdeMO", 7: "Type 2", 8: "Type 3A", 10: "Wall (Euro)",
    13: "CCS1", 14: "Three Phase EU", 15: "Caravan Mains Socket", 20: "CCS2", 24: "Type 3A",
}

def map_status(status: str) -> str:
    """Map JSON status to DB enum"""
    if status == "AVAILABLE": 
        return "available"
    if status == "CHARGING": 
        return "charging"
    if status in ("OUTOFORDER", "UNDERREPAIR"): 
        return "malfunction"
    return "offline"

def round_decimal(value, decimals: int):
    """Safe decimal rounding for lat/lon"""
    if value is None: 
        return 0.0
    try:
        numeric_value = float(value)
        factor = 10 ** decimals
        return int(round(numeric_value * factor)) / factor
    except (ValueError, TypeError):
        return 0.0

def safe_int(value, default=0):
    """Safe conversion to int for power etc."""
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def insert_from_json(conn, cursor, json_path: Path, max_locations: int = None):
    """
    Εισάγει ΟΛΑ τα δεδομένα από JSON -> DB (χωρίς limit)
    """
    try:
        with json_path.open("r", encoding="utf-8") as f:
            locations = json.load(f)
    except Exception as e:
        print(f"JSON parse error: {e}")
        return 0

    inserted_stations = 0
    for idx, loc in enumerate(locations):
        if max_locations is not None and idx >= max_locations: 
            break

        try:
            # Station INSERT - safe values
            cursor.execute("""
                INSERT INTO station (address, Latitude, Longitude, name, provider) 
                VALUES (%s, %s, %s, %s, %s)
            """, (
                loc.get("address", ""),
                round_decimal(loc.get("latitude"), 4),
                round_decimal(loc.get("longitude"), 4),
                loc.get("name", f"Station {idx+1}"), 
                "ElectroWay"
            ))
            
            station_id = cursor.lastrowid
            inserted_stations += 1

            # Outlets INSERT - safe values
            is_fast = 1 if loc.get("is_fast_charger") else 0
            stations_list = loc.get("stations", [])
            
            for st in stations_list:
                outlets_list = st.get("outlets", [])
                for out in outlets_list:
                    connector_id = out.get("connector")
                    connector = CONNECTOR_MAP.get(connector_id, f"connector{connector_id}")
                    power = safe_int(out.get("kilowatts"))
                    state = map_status(out.get("status", "offline"))
                    markup = random_markup()

                    cursor.execute("""
                        INSERT INTO outlet (stationid, connector, power, state, is_fast, markup) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (station_id, connector, power, state, is_fast, markup))
        
        except Exception as e:
            print(f"Error inserting station {idx}: {e}")
            continue  # Skip problematic station, continue with next
    
    conn.commit()
    return inserted_stations