from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Path
from fastapi.responses import JSONResponse
import mysql.connector

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

MAX_MINUTES = 60
MIN_MINUTES = 30

# user specified mins
@router.post("/reserve/{point_id}/{minutes}")
async def reserve_with_specified_minutes(
    request: Request,
    point_id: int = Path(..., ge=1),
    minutes: int = Path(..., ge=1) # must provide
):
    """
    POST /api/reserve/{point_id}/{minutes}
    User specified minutes
    """
    
    if minutes < MIN_MINUTES:
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT state FROM outlet WHERE outletid = %s", (point_id,))
            point = cursor.fetchone()
            status = point['state'] if point else "not_found"
            cursor.close()
            conn.close()
        except:
            status = "unknown"
        
        return {
            "pointid": point_id,
            "status": status,
            "reservationendtime": "1970-01-01 00:00"
        }
    
    # mins>29, keep min(mins, 60)
    actual_minutes = min(minutes, MAX_MINUTES)
    
    return await _reserve_logic(request, point_id, actual_minutes)

# user did not specify mins
@router.post("/reserve/{point_id}")
async def reserve_without_minutes(
    request: Request,
    point_id: int = Path(..., ge=1)
):
    """
    POST /api/reserve/{point_id}
    User didn't specify minutes
    """
    return await _reserve_logic(request, point_id, MIN_MINUTES)

# shared logic for both cases
async def _reserve_logic(request: Request, point_id: int, minutes: int):
    """
    Shared reservation logic for both patterns
    minutes is GUARANTEED to be: 30 ≤ minutes ≤ 60
    """
    # double check
    if minutes < MIN_MINUTES or minutes > MAX_MINUTES:
        raise ValueError(f"Minutes {minutes} outside valid range 30-60")
    
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT outletid, state FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()
        
        if not point:
            return {
                "pointid": point_id,
                "status": "not_found",
                "reservationendtime": "1970-01-01 00:00"
            }
        
        if point['state'] != 'available':
            return {
                "pointid": point_id,
                "status": point['state'],
                "reservationendtime": "1970-01-01 00:00"
            }
        
        now = datetime.now()
        reservation_end = now + timedelta(minutes=minutes)
        formatted_end_time = reservation_end.strftime("%Y-%m-%d %H:%M")
        
        cursor.execute("UPDATE outlet SET state = 'reserved' WHERE outletid = %s", (point_id,))

        cursor.execute("""
            INSERT INTO reservation 
            (date, reservationtime, reservationexpiry, has_charged, pointid, userid) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            now.date(),
            now,
            reservation_end,
            0,
            point_id,
            None
        ))
        
        conn.commit()
        
        # success response
        return {
            "pointid": point_id,
            "status": "reserved",
            "reservationendtime": formatted_end_time
        }
            
    except mysql.connector.Error as db_error:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        error = build_error_log(request, 400, "Database error", str(db_error))
        return JSONResponse(status_code=400, content=error)
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        error = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=error)
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()