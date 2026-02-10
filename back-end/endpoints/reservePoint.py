from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Path
from fastapi.responses import JSONResponse
import mysql.connector

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}

MAX_MINUTES = 60
MIN_MINUTES = 1    # either 30 or 1

# user specified mins
@router.post("/reserve/{point_id}/{minutes}")
async def reserve_with_specified_minutes(
    request: Request,
    point_id: int = Path(..., ge=1),
    minutes: int = Path(..., ge=1)
):
    return await reserve(request, point_id, minutes)

# user did not specify mins
@router.post("/reserve/{point_id}")
async def reserve_without_minutes(
    request: Request,
    point_id: int = Path(..., ge=1)
):
    return await reserve(request, point_id, MIN_MINUTES)

# shared logic for both cases
async def reserve(request: Request, point_id: int, minutes: int):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=True)
        cursor.execute("SELECT outletid, state FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()

        # check if point exists
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
        if (minutes<MIN_MINUTES) or (status!='available'):
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
        
        cursor.execute("UPDATE outlet SET state = 'reserved' WHERE outletid = %s", (point_id,))

        # dummy user for now
        cursor.execute("SELECT userid FROM users")
        user = cursor.fetchone()
        userid = user['userid']

        cursor.execute("""
            INSERT INTO reservation 
            (date, reservationtime, reservationexpiry, has_charged, userid, pointid, sessionid) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
            now.date(),
            now,
            reservation_end,
            0,
            userid,
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
        if cursor is not None:
            try:
                cursor.close()
            except:
                pass
        if conn is not None and conn.is_connected():
            try:
                conn.close()
            except:
                pass






######
######
#
# κανει το ιδιο με το reserve απλα με αλλο λινκ για να παρει userid
#
###### 
######



@router.post("/reserve-custom/{point_id}/{minutes}/{user_id}")
async def reserve_custom(
    request: Request,
    point_id: int = Path(..., ge=1),
    minutes: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1)
):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=True)

        # ελεγχος αν υπάρχει ο φορτιστής
        cursor.execute("SELECT outletid, state FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()

        if not point:
            error = build_error_log(request, 404, "Not found", f"Charging point {point_id} does not exist")
            return JSONResponse(status_code=404, content=error)

        status = point['state']

        if (minutes < MIN_MINUTES) or (status != 'available'):
            return {
                "pointid": str(point_id), # Επιστρέφουμε string για τυπικότητα
                "status": status,
                "reservationendtime": "1970-01-01 00:00"
            }
        
        # ελεγχος αν είναι διαθέσιμος
        if status != 'available':
            return {
                "pointid": point_id,
                "status": status,
                "reservationendtime": "1970-01-01 00:00"
            }

        # 3. Υπολογισμός χρόνου λήξης
        now = datetime.now()
        reservation_mins = min(minutes, MAX_MINUTES)
        reservation_end = now + timedelta(minutes=reservation_mins)
        formatted_end_time = reservation_end.strftime("%Y-%m-%d %H:%M")
        
        #  Ενημέρωση κατάστασης φορτιστή
        cursor.execute("UPDATE outlet SET state = 'reserved' WHERE outletid = %s", (point_id,))

        #  Εισαγωγή κράτησης με το ΣΩΣΤΟ userid
        cursor.execute("""
            INSERT INTO reservation 
            (date, reservationtime, reservationexpiry, has_charged, userid, pointid, sessionid) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                now.date(),
                now,
                reservation_end,
                0,
                user_id,  # Το ID που πήραμε από το URL
                point_id,
                None
            ))
        
        conn.commit()
        
        return {
            "pointid": point_id,
            "status": "reserved",
            "reservationendtime": formatted_end_time
        }
            
    except Exception as e:
        if conn: conn.rollback()
        error = build_error_log(request, 500, "Internal server error", str(e))
        return JSONResponse(status_code=500, content=error)
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if conn and conn.is_connected():
            try:
                conn.close()
            except:
                pass