# ΚΑΝΕΙ ΤΟ ΙΔΙΟ ΜΕ ΑΥΤΟ ΤΟΥ API ΑΠΛΑ ΜΕ ΑΛΛΟ URL ΠΟΥ ΘΑ ΠΑΡΕΙ ΚΑΙ ΤΟ USERID

# backend/endpoints/usecase_reservation.py
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Path
from fastapi.responses import JSONResponse
import mysql.connector
from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["usecase_reserve"])

MAX_MINUTES = 60
MIN_MINUTES = 1

@router.post("/reserve-custom/{point_id}/{minutes}/{user_id}")
async def reserve_custom(
    request: Request,
    point_id: int = Path(..., ge=1),
    minutes: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1)
):
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
        if cursor: cursor.close()
        if conn and conn.is_connected(): conn.close()