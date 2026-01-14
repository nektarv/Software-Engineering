from fastapi import APIRouter, Request, Response, Path
from fastapi.responses import JSONResponse
import mysql.connector
from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

@router.post("/favourites/{userid}/{stationid}")
def add_favourite(
    request: Request,
    userid: int = Path(..., ge=1),
    stationid: int = Path(..., ge=1),
):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Insert ignore avoids crashing if already favourited (because PK is userid+stationid)
        cur.execute(
            "INSERT IGNORE INTO favourites (userid, stationid) VALUES (%s, %s)",
            (userid, stationid),
        )
        conn.commit()

        cur.close()
        conn.close()
        return {"ok": True}

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)

@router.delete("/favourites/{userid}/{stationid}")
def remove_favourite(
    request: Request,
    userid: int = Path(..., ge=1),
    stationid: int = Path(..., ge=1),
):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute(
            "DELETE FROM favourites WHERE userid = %s AND stationid = %s",
            (userid, stationid),
        )
        conn.commit()

        cur.close()
        conn.close()
        return {"ok": True}

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
