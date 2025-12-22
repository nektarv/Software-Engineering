from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector

from utils import DB_CONFIG, build_error_log

router = APIRouter()  



@router.get("/admin/healthcheck")
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