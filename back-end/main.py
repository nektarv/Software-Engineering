from fastapi import FastAPI
import mysql.connector

DB_CONFIG = {
    "host": "localhost",
    "user": "root",          
    "password": "Nickmpamias26!",
    "database": "charging_database",
}

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"} # δεν ηξερα τι να βαλω εδω (Νικος)



from datetime import datetime
from fastapi import Request
from fastapi.responses import JSONResponse

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
        "return_code": code,
        "error": description,
        "debuginfo": f"{error_text}: {raw_debuginfo}",
    }


@app.get("/admin/healthcheck")
def admin_healthcheck(request: Request):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # number of charging points (outlets)
        cursor.execute("SELECT COUNT(*) FROM outlet")
        n_charge_points = cursor.fetchone()[0]

        # online charge points: all outlets with active network communication
        # (available, charging, reserved, malfunction)
        cursor.execute(
            "SELECT COUNT(*) FROM outlet "
            "WHERE state IN ('available', 'charging', 'reserved', 'malfunction')"
        )
        n_online = cursor.fetchone()[0]

        # offline
        cursor.execute(
            "SELECT COUNT(*) FROM outlet "
            "WHERE state = 'offline'"
        )
        n_offline = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "status": "OK",
            "dbconnection": f"mysql://{DB_CONFIG['user']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}",
            "n_charge_points": n_charge_points,
            "n_charge_points_online": n_online,
            "n_charge_points_offline": n_offline,
        }
    except Exception as e:
        error_body = build_error_log(
            request=request,
            code=400,
            error_text="Healthcheck failed",
            raw_debuginfo=str(e),
        )
        return JSONResponse(status_code=400, content=error_body)