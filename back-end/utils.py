from datetime import datetime
from fastapi import Request
import mysql.connector


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root", #change it back to root before commit
    "database": "charging_database",
}


def build_error_log(request: Request, code: int, error_text: str, raw_debuginfo: str):
    # try to read description from errorcodes table
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM errorcodes WHERE code = %s", (code,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()


        if row:
            description = row[0]
        else:
            description = "Unmapped error code"
    except Exception:
        description = "Error while reading \"errorcodes\" table"


    # compute originator_value
    if request.client:
        originator_value = request.client.host
    else:
        originator_value = "unknown"


    return {
        "call": str(request.url),
        "timeref": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "originator": originator_value,
        "returncode": code,
        "error": description,
        "debuginfo": f"{error_text}: {raw_debuginfo}",
    }
