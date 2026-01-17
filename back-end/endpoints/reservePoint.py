from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Path, Query, HTTPException
from fastapi.responses import JSONResponse
import mysql.connector

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}

MAX_MINUTES = 60
MIN_MINUTES = 30    # either 30 or 1

# user specified mins
@router.post("/reserve/{point_id}/{minutes}")
async def reserve_with_specified_minutes(
    request: Request,
    point_id: int = Path(..., ge=1),
    minutes: int = Path(..., ge=1),
    user_id: int = Query(..., description="User ID making the reservation")
):
    return await reserve(request, point_id, minutes, user_id)

# user did not specify mins
@router.post("/reserve/{point_id}")
async def reserve_without_minutes(
    request: Request,
    point_id: int = Path(..., ge=1),
    user_id: int = Query(..., description="User ID making the reservation")
):
    return await reserve(request, point_id, MIN_MINUTES, user_id)

# shared logic for both cases
async def reserve(request: Request, point_id: int, minutes: int, user_id: int):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # Check if user exists
        cursor.execute("SELECT userid FROM users WHERE userid = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            error = build_error_log(
                request, 400, "Bad request",
                f"User with ID {user_id} does not exist"
            )
            return JSONResponse(status_code=400, content=error)
        
        # Check if point exists
        cursor.execute("SELECT outletid, state FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()

        if not point:
            error = build_error_log(
                request, 404, "Not found",
                f"Charging point {point_id} does not exist"
            )
            return JSONResponse(status_code=404, content=error)

        status = point['state']
        # check for valid status
        if status not in ALLOWED_STATUSES:
            error = build_error_log(
                request, 400, "Bad request",
                f"Invalid status"
            )
            return JSONResponse(status_code=400, content=error)   

        # check for valid minutes and correct status
        if (minutes < MIN_MINUTES) or (status != 'available'):
            return {
                "pointid": point_id,
                "status": status,
                "reservationendtime": "1970-01-01 00:00"
            }
    
        # ----------------------------------------------
        # we have a valid reservation, let's submit it
        # ----------------------------------------------
        
        # compute reservation end time
        now = datetime.now()
        reservation_mins = min(minutes, MAX_MINUTES)
        reservation_end = now + timedelta(minutes=reservation_mins)
        formatted_end_time = reservation_end.strftime("%Y-%m-%d %H:%M")
        
        # Update outlet status
        cursor.execute("UPDATE outlet SET state = 'reserved' WHERE outletid = %s", (point_id,))

        # Create reservation with actual user ID
        cursor.execute("""
            INSERT INTO reservation 
            (date, reservationtime, reservationexpiry, has_charged, userid, pointid, sessionid) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
            now.date(),
            now,
            reservation_end,
            0,
            user_id,  # Use the actual user_id parameter
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