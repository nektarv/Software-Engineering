from fastapi import APIRouter, Request, Response, Query, Path
from fastapi.responses import JSONResponse, PlainTextResponse
import mysql.connector
from datetime import datetime, timedelta

from management.utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])


def _rows_to_csv(rows, header):
    lines = [",".join(header)]
    for r in rows:
        lines.append(",".join("" if r.get(k) is None else str(r.get(k)) for k in header))
    return "\n".join(lines) + "\n"


def _parse_yyyymmdd(s: str) -> datetime:
    return datetime.strptime(s, "%Y%m%d")


@router.get("/pointstatus/{point_id}/{date_from}/{date_to}")
def get_point_status(
    request: Request,
    point_id: int = Path(..., ge=1),
    date_from: str = Path(..., min_length=8, max_length=8),
    date_to: str = Path(..., min_length=8, max_length=8),
    format: str = Query(default="json"),
):
    """
    (g) GET /api/pointstatus/{pointid}/{from}/{to}?format=json|csv
    Uses updates table populated by trigger on outlet state changes.
    """
    if format not in ("json", "csv"):
        payload = build_error_log(request, 400, "Bad request", f"Invalid format '{format}'")
        return JSONResponse(status_code=400, content=payload)

    try:
        dt_from = _parse_yyyymmdd(date_from)
        dt_to = _parse_yyyymmdd(date_to)
        if dt_to < dt_from:
            payload = build_error_log(request, 400, "Bad request", "date_to earlier than date_from")
            return JSONResponse(status_code=400, content=payload)

        start_ts = dt_from.strftime("%Y-%m-%d 00:00:00")
        end_ts = (dt_to + timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")  # exclusive

        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor(dictionary=True)

        sql = """
            SELECT
              outletid AS pointid,
              old_state,
              new_state,
              timeref
            FROM updates
            WHERE outletid = %s
              AND timeref >= %s
              AND timeref < %s
            ORDER BY timeref ASC
        """
        cur.execute(sql, (point_id, start_ts, end_ts))
        rows = cur.fetchall()

        for r in rows:
            if r.get("timeref"):
                r["timeref"] = r["timeref"].strftime("%Y-%m-%d %H:%M")

        cur.close()
        conn.close()

        if not rows:
            return Response(status_code=204)

        if format == "csv":
            header = ["pointid", "old_state", "new_state", "timeref"]
            csv_text = _rows_to_csv(rows, header)
            return PlainTextResponse(content=csv_text, media_type="text/csv; charset=utf-8")

        return rows

    except ValueError as e:
        payload = build_error_log(request, 400, "Bad request", f"Invalid date format: {e}")
        return JSONResponse(status_code=400, content=payload)
    except mysql.connector.Error as e:
        payload = build_error_log(request, 400, "Database error", str(e))
        return JSONResponse(status_code=400, content=payload)
    except Exception as e:
        payload = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=payload)
