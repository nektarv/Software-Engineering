from fastapi import APIRouter, Request, Response, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import mysql.connector
from datetime import datetime

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

ALLOWED_FORMATS = {"json", "csv"}
ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}

def _empty_to_none(v):
    if v is None:
        return None
    if isinstance(v, str) and v.strip() == "":
        return None
    return v

def _to_float_or_none(v):
    v = _empty_to_none(v)
    if v is None:
        return None
    return float(v)

def _to_int_or_none(v):
    v = _empty_to_none(v)
    if v is None:
        return None
    return int(v)


def _rows_to_csv(rows, header):
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join("" if r.get(k) is None else str(r.get(k)) for k in header))
    return "\n".join(lines) + "\n"


def _parse_price_time(price_time: str | None) -> str | None:
    """
    Accept YYYYMMDDHH (e.g. 2025011316).
    Returns MySQL DATETIME string "YYYY-MM-DD HH:00:00".
    None means "current time".
    """
    if price_time is None:
        return None
    if len(price_time) != 10 or not price_time.isdigit():
        raise ValueError("price_time must be YYYYMMDDHH")
    dt = datetime.strptime(price_time, "%Y%m%d%H")
    return dt.strftime("%Y-%m-%d %H:00:00")


def _get_dam_price_or_error(cur, request: Request, target_ts: str | None):
    """
    Fetch DAM price at or before target time.
    - If target_ts is None => use NOW()
    - If DAM table empty => 400
    - If target_ts beyond max available => 400
    - If no DAM price <= target => 400
    Returns: float dam_price
    """
    # Max available DAM timestamp
    cur.execute("SELECT MAX(timeref) AS max_ts FROM dam_prices")
    mx = cur.fetchone()
    max_ts = mx["max_ts"] if mx else None

    if max_ts is None:
        return None, JSONResponse(
            status_code=400,
            content=build_error_log(request, 400, "Bad request", "DAM prices table is empty"),
        )

    # If user requested a specific time and it is beyond max available => error
    if target_ts is not None:
        # Compare in MySQL safely
        cur.execute("SELECT (%s > %s) AS beyond", (target_ts, max_ts.strftime("%Y-%m-%d %H:%M:%S")))
        beyond = cur.fetchone()["beyond"]
        if beyond == 1:
            msg = (
                f"No DAM data for requested time {target_ts}. "
                f"Available up to {max_ts.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return None, JSONResponse(
                status_code=400,
                content=build_error_log(request, 400, "Bad request", msg),
            )

    # Fetch DAM at or before target
    if target_ts is None:
        cur.execute(
            """
            SELECT price_eur_per_kwh
            FROM dam_prices
            WHERE timeref <= NOW()
            ORDER BY timeref DESC
            LIMIT 1
            """
        )
    else:
        cur.execute(
            """
            SELECT price_eur_per_kwh
            FROM dam_prices
            WHERE timeref <= %s
            ORDER BY timeref DESC
            LIMIT 1
            """,
            (target_ts,),
        )

    dam = cur.fetchone()
    if dam is None or dam.get("price_eur_per_kwh") is None:
        msg = "No DAM price available at or before requested time"
        return None, JSONResponse(
            status_code=400,
            content=build_error_log(request, 400, "Bad request", msg),
        )

    return float(dam["price_eur_per_kwh"]), None


@router.get("/chargers")
def list_chargers(
    request: Request,
    # Filters
    min_price: str | None = Query(default=None),
    max_price: str | None = Query(default=None),
    location_q: str | None = Query(default=None),
    connector: str | None = Query(default=None),
    min_power: str | None = Query(default=None),
    max_power: str | None = Query(default=None),
    status: str | None = Query(default=None),  # only applied when viewing non-current
    only_fast: int | None = Query(default=None),  # 0/1


    # Favourites
    userid: str | None = Query(default=None),
    favourites_only: int = Query(default=0),  # 0/1

    # Price time
    price_time: str | None = Query(default=None),  # YYYYMMDDHH

    # Output format
    format: str = Query(default="json"),
):
    min_price = _to_float_or_none(min_price)
    max_price = _to_float_or_none(max_price)
    min_power = _to_int_or_none(min_power)
    max_power = _to_int_or_none(max_power)
    userid = _to_int_or_none(userid)

    # Validate basic params
    if format not in ALLOWED_FORMATS:
        payload = build_error_log(request, 400, "Bad request", f"Invalid format '{format}'")
        return JSONResponse(status_code=400, content=payload)

    if status is not None and status not in ALLOWED_STATUSES:
        payload = build_error_log(request, 400, "Bad request", f"Invalid status '{status}'")
        return JSONResponse(status_code=400, content=payload)

    if only_fast is not None and only_fast not in (0, 1):
        payload = build_error_log(request, 400, "Bad request", "only_fast must be 0 or 1")
        return JSONResponse(status_code=400, content=payload)

    if favourites_only not in (0, 1):
        payload = build_error_log(request, 400, "Bad request", "favourites_only must be 0 or 1")
        return JSONResponse(status_code=400, content=payload)

    if favourites_only == 1 and userid is None:
        payload = build_error_log(request, 400, "Bad request", "userid required when favourites_only=1")
        return JSONResponse(status_code=400, content=payload)

    # Parse price_time
    try:
        target_ts = _parse_price_time(price_time)  # None => current
    except ValueError as e:
        payload = build_error_log(request, 400, "Bad request", str(e))
        return JSONResponse(status_code=400, content=payload)

    is_current_time_view = (target_ts is None)

    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        # DAM price fetch + strict error handling
        dam_price, dam_error_response = _get_dam_price_or_error(cur, request, target_ts)
        if dam_error_response is not None:
            cur.close()
            conn.close()
            return dam_error_response

        # Base query
        sql = """
            SELECT
                o.outletid AS pointid,
                s.stationid AS stationid,
                s.name AS station_name,
                s.address AS address,
                s.Latitude AS lat,
                s.Longitude AS lon,

                o.connector AS connector,
                o.power AS power,
                o.state AS status,
                o.is_fast AS is_fast,

                ROUND(%s * o.markup, 4) AS kwhprice,

                CASE
                  WHEN %s IS NULL THEN 0
                  WHEN f.userid IS NULL THEN 0
                  ELSE 1
                END AS is_favourite,

                %s AS can_show_on_map,
                CASE
                  WHEN %s = 1 AND o.state = 'available' THEN 1 ELSE 0
                END AS can_reserve

            FROM outlet o
            JOIN station s ON s.stationid = o.stationid
            LEFT JOIN favourites f
              ON f.stationid = s.stationid AND f.userid = %s
            WHERE 1=1
        """

        params = [
            dam_price,                      # %s in ROUND()
            userid,                         # %s in is_favourite CASE
            1 if is_current_time_view else 0,  # can_show_on_map
            1 if is_current_time_view else 0,  # can_reserve CASE flag
            userid,                         # %s in favourites join
        ]

        # Enforce your rule-set (backend guarantee)
        if is_current_time_view:
            # Current: only available
            sql += " AND o.state = 'available'"
        else:
            # Historical: exclude out-of-service
            sql += " AND o.state NOT IN ('offline', 'malfunction')"
            # Optional status filter only makes sense in historical view
            if status is not None:
                sql += " AND o.state = %s"
                params.append(status)

        # Other filters
        if location_q:
            sql += " AND (s.name LIKE %s OR s.address LIKE %s)"
            like = f"%{location_q}%"
            params.extend([like, like])

        if connector:
            sql += " AND o.connector = %s"
            params.append(connector)

        if only_fast is not None:
            sql += " AND o.is_fast = %s"
            params.append(only_fast)

        if min_power is not None:
            sql += " AND o.power >= %s"
            params.append(min_power)

        if max_power is not None:
            sql += " AND o.power <= %s"
            params.append(max_power)

        if min_price is not None:
            sql += " AND ROUND(%s * o.markup, 4) >= %s"
            params.extend([dam_price, min_price])

        if max_price is not None:
            sql += " AND ROUND(%s * o.markup, 4) <= %s"
            params.extend([dam_price, max_price])

        if favourites_only == 1:
            sql += " AND f.userid IS NOT NULL"

        sql += " ORDER BY kwhprice ASC, power DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()

        cur.close()
        conn.close()

        if not rows:
            return Response(status_code=204)

        if format == "csv":
            header = [
                "pointid", "stationid", "station_name", "address", "lat", "lon",
                "connector", "power", "status", "kwhprice", "is_favourite",
                "can_show_on_map", "can_reserve"
            ]
            csv_text = _rows_to_csv(rows, header)
            return PlainTextResponse(content=csv_text, media_type="text/csv; charset=utf-8")

        return rows

    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
