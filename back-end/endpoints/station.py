from fastapi import APIRouter, Request, Response, Query, Path
from fastapi.responses import JSONResponse, PlainTextResponse
import mysql.connector
from datetime import datetime

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["map/list/filters"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}


def _rows_to_csv(rows, header):
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join("" if r.get(k) is None else str(r.get(k)) for k in header))
    return "\n".join(lines) + "\n"

#This is just a variant of points with geographical limits. Not significantly different
@router.get("/stations")
def get_stations(
    request: Request,
    lat: float | None = Query(default=None),
    lon: float | None = Query(default=None),
    range: float | None = Query(default=None),
    status: str | None = Query(default=None),
    format: str = Query(default="json"),
):

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
                o.state AS status,
                s.stationid AS stationid
            FROM outlet o
            JOIN station s ON s.stationid = o.stationid
        """

        conditions = []
        params = []

        # ✅ Add geo filter ONLY if lat, lon AND range are all provided
        if lat is not None and lon is not None and range is not None:
            conditions.append("s.Latitude BETWEEN %s AND %s")
            conditions.append("s.Longitude BETWEEN %s AND %s")
            params.extend([
                lat - range,
                lat + range,
                lon - range,
                lon + range
            ])

        # Optional status filter
        if status is not None:
            conditions.append("o.state = %s")
            params.append(status)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        cur.execute(sql, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        if not rows:
            return Response(status_code=204)

        if format == "csv":
            csv_text = _rows_to_csv(rows, ["pointid", "lon", "lat", "cap", "status","stationid"])
            return PlainTextResponse(content=csv_text, media_type="text/csv; charset=utf-8")

        return rows

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
    




#
#
#This should fetch a single station and all its outlets.
#
#

@router.get("/station-details/{station_id}")
def get_station_details(
    request: Request,
    station_id: int = Path(..., ge=1),
    user_id: int | None = Query(default=None)
):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        # Fetch ALL outlets for this station + favourite status for this user
        sql_points = """
            SELECT 
                o.outletid AS pointid,
                s.stationid AS stationid,
                s.Longitude AS lon,
                s.Latitude AS lat,
                o.power AS cap,
                o.state AS status,
                o.connector AS connector,
                o.markup AS markup,
                s.provider AS provider,
                s.address AS db_address,
                CASE 
                    WHEN f.userid IS NOT NULL THEN 1 
                    ELSE 0 
                END AS is_favourite
            FROM outlet o
            JOIN station s ON s.stationid = o.stationid
            LEFT JOIN favourites f ON f.stationid = s.stationid AND f.userid = %s
            WHERE s.stationid = %s
        """

        cur.execute(sql_points, (user_id, station_id))
        rows = cur.fetchall()

        if not rows:
            cur.close()
            conn.close()
            return Response(status_code=204)

        # Fetch latest DAM price once
        sql_dam = """
            SELECT price_eur_per_kwh
            FROM dam_prices
            WHERE timeref <= NOW()
            ORDER BY timeref DESC
            LIMIT 1
        """
        cur.execute(sql_dam)
        dam = cur.fetchone()
        base_price = None
        if dam and dam.get("price_eur_per_kwh") is not None:
            base_price = float(dam["price_eur_per_kwh"])

        # Build outlets list
        outlets = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for row in rows:
            reservation_end = None

            # Reservation logic per outlet (only if currently reserved)
            if (row.get("status") or "").lower() == "reserved":
                sql_res = """
                    SELECT reservationexpiry
                    FROM reservation
                    WHERE pointid = %s AND reservationexpiry >= NOW()
                    ORDER BY reservationexpiry DESC
                    LIMIT 1
                """
                cur.execute(sql_res, (row["pointid"],))
                res = cur.fetchone()
                if res and res.get("reservationexpiry"):
                    reservation_end = res["reservationexpiry"].strftime("%Y-%m-%d %H:%M:%S")
                else:
                    reservation_end = now_str  # fallback (keeps your previous behavior)

            # Price logic per outlet (markup differs per outlet)
            kwhprice = None
            if base_price is not None and row.get("markup") is not None:
                kwhprice = round(base_price * float(row["markup"]), 4)

            outlets.append({
                "pointid": int(row["pointid"]),
                "cap": int(row["cap"]) if row["cap"] is not None else 0,
                "status": row["status"],
                "reservationendtime": reservation_end,  # None if not reserved
                "kwhprice": kwhprice,
                "connector": row["connector"],
            })

        # Station-level fields (same for all rows, take from first)
        first = rows[0]

        payload = {
            "stationid": int(first["stationid"]),
            "lon": float(first["lon"]),
            "lat": float(first["lat"]),
            "provider": first["provider"] or "unknown",
            "address": first["db_address"] if first["db_address"] else "Address not available",
            "is_favourite": int(first["is_favourite"]),
            "outlets": outlets
        }

        cur.close()
        conn.close()
        return payload

    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
