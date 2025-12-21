from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector
from typing import Optional

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

@router.post("/reserve/{point_id}")
async def reserve_point(
    request: Request,
    point_id: int,
    minutes: Optional[int] = 30
):
    """
    (c) POST /api/reserve/{point_id}?minutes=XX
    Reserve a charging point.
    """
    
    MAX_MINUTES = 60
    actual_minutes = min(minutes, MAX_MINUTES) if minutes else 30
    
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # Check if point exists and is available
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
        
        # Calculate times
        now = datetime.now()
        reservation_end = now + timedelta(minutes=actual_minutes)
        formatted_end_time = reservation_end.strftime("%Y-%m-%d %H:%M")
        
        # NO TRANSACTION - just execute sequentially
        # 1. Update outlet status
        cursor.execute("UPDATE outlet SET state = 'reserved' WHERE outletid = %s", (point_id,))
        
        # 2. Create reservation
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
            None  # Change if you have user authentication
        ))
        
        # 3. Commit both operations
        conn.commit()
        
        return {
            "pointid": point_id,
            "status": "reserved",
            "reservationendtime": formatted_end_time
        }
            
    except mysql.connector.Error as db_error:
        # Try to rollback if something failed
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