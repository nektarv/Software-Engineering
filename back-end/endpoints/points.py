from fastapi import APIRouter, Request, Response, Query, Path
from fastapi.responses import JSONResponse, PlainTextResponse
import mysql.connector
from datetime import datetime

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}


def _rows_to_csv(rows, header):
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join("" if r.get(k) is None else str(r.get(k)) for k in header))
    return "\n".join(lines) + "\n"


@router.get("/points")
def get_points(
    request: Request,
    status: str | None = Query(default=None),
    format: str = Query(default="json"),
):
    """
    (a) GET /api/points?status=...&format=json|csv
    Returns outlet list with station lat/lon.
    """
    if status is not None and status not in ALLOWED_STATUSES:
        payload = build_error_log(request, 400, "Bad request", f"Invalid status '{status}'")
        return JSONResponse(status_code=400, content=payload)

    if format not in ("json", "csv"):
        payload = build_error_log(request, 400, "Bad request", f"Invalid format '{format}'")
        return JSONResponse(status_code=400, content=payload)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        sql = """
            SELECT
                o.outletid AS pointid,
                s.Longitude AS lon,
                s.Latitude AS lat,
                o.power AS cap,
                o.state AS status
            FROM outlet o
            JOIN station s ON s.stationid = o.stationid
        """
        params = []
        if status is not None:
            sql += " WHERE o.state = %s"
            params.append(status)

        cur.execute(sql, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        if not rows:
            return Response(status_code=204)

        if format == "csv":
            csv_text = _rows_to_csv(rows, ["pointid", "lon", "lat", "cap", "status"])
            return PlainTextResponse(content=csv_text, media_type="text/csv; charset=utf-8")

        return rows

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)


@router.get("/point/{point_id}")
def get_point(
    request: Request,
    point_id: int = Path(..., ge=1),
):
    """
    (b) GET /api/point/{id}
    Returns point details + reservationendtime + computed kwhprice using DAM * markup.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        # Outlet + station
        sql_point = """
            SELECT
                o.outletid AS pointid,
                s.Longitude AS lon,
                s.Latitude AS lat,
                o.power AS cap,
                o.state AS status,
                o.markup AS markup,
                s.provider AS provider
            FROM outlet o
            JOIN station s ON s.stationid = o.stationid
            WHERE o.outletid = %s
            LIMIT 1
        """
        cur.execute(sql_point, (point_id,))
        row = cur.fetchone()

        if row is None:
            cur.close()
            conn.close()
            return Response(status_code=204)

        # reservationendtime: "now" unless reserved & has active reservation
        reservation_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if row["status"] == "reserved":
            sql_res = """
                SELECT reservationexpiry
                FROM reservation
                WHERE pointid = %s
                  AND reservationexpiry >= NOW()
                ORDER BY reservationexpiry DESC
                LIMIT 1
            """
            cur.execute(sql_res, (point_id,))
            res = cur.fetchone()
            if res and res.get("reservationexpiry") is not None:
                reservation_end = res["reservationexpiry"].strftime("%Y-%m-%d %H:%M:%S")

        # DAM latest price
        sql_dam = """
            SELECT price_eur_per_kwh
            FROM dam_prices
            WHERE timeref <= NOW()
            ORDER BY timeref DESC
            LIMIT 1
        """
        cur.execute(sql_dam)
        dam = cur.fetchone()

        if dam is None or dam.get("price_eur_per_kwh") is None:
            # If DAM table empty, return null price (or you can 400)
            kwhprice = None
        else:
            kwhprice = round(float(dam["price_eur_per_kwh"]) * float(row["markup"]), 4)

        cur.close()
        conn.close()

        payload = {
            "pointid": int(row["pointid"]),
            "lon": float(row["lon"]),
            "lat": float(row["lat"]),
            "cap": int(row["cap"]) if row["cap"] is not None else 0,
            "status": row["status"],
            "reservationendtime": reservation_end,
            "kwhprice": kwhprice,
            "provider": row["provider"] or "unknown",
        }
        return payload

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
