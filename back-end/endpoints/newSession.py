from datetime import datetime
from fastapi import APIRouter, Request, Path, Body
from fastapi.responses import JSONResponse
import mysql.connector
from pydantic import BaseModel
from typing import Optional

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["sessions"])

class SessionRequest(BaseModel):
    pointid: int
    starttime: str
    endtime: str
    startsoc: int
    endsoc: int
    totalkwh: float
    kwhprice: float
    amount: float

@router.post("/newsession")
async def new_session(
    request: Request,
    session_data: SessionRequest = Body(...)
):
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        # -----------------------------        
        # check if input data is valid
        # -----------------------------

        # check if point exists
        cursor.execute("SELECT * FROM outlet WHERE outletid = %s", (session_data.pointid,))
        point = cursor.fetchone()
        if not point:
            error = build_error_log(
                request, 404, "Not found",
                f"Charging point {session_data.pointid} does not exist"
            )
            return JSONResponse(status_code=404, content=error)

        # dates in right format
        try:
            start_dt = datetime.strptime(session_data.starttime, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(session_data.endtime, "%Y-%m-%d %H:%M")
        except ValueError:
            error = build_error_log(
                request, 400, "Bad request",
                "Invalid date/time format"
            )
            return JSONResponse(status_code=400, content=error)
        
        # end time > start time
        if end_dt <= start_dt:
            error = build_error_log(
                request, 400, "Bad request",
                "End time must be after start time"
            )
            return JSONResponse(status_code=400, content=error)
        
        # valid starting battery 
        if not (0 <= session_data.startsoc <= 100):
            error = build_error_log(
                request, 400, "Bad request",
                "Battery before charging must be within 0-100"
            )
            return JSONResponse(status_code=400, content=error)
        
        # valid ending battery
        if not (0 <= session_data.endsoc <= 100):
            error = build_error_log(
                request, 400, "Bad request",
                "Battery after charging must be within 0-100"
            )
            return JSONResponse(status_code=400, content=error)
        
        # ending battery >= starting battery
        if session_data.endsoc < session_data.startsoc:
            error = build_error_log(
                request, 400, "Bad request",
                "Battery percentage can't decrease"
            )
            return JSONResponse(status_code=400, content=error)
        
        # total kWh > 0
        if session_data.totalkwh <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "Total kWh used must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        # kWh price > 0
        if session_data.kwhprice <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "kWh price must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        # amount payed > 0
        if session_data.amount <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "Amount payed must be positive"
            )
            return JSONResponse(status_code=400, content=error)

        # amount matches up with total kwh (times) kwh price
        expected_amount = session_data.totalkwh * session_data.kwhprice
        if abs(session_data.amount - expected_amount) > 0.001: # allow rounding differences
            error = build_error_log(
                request, 400, "Bad request",
                "Amount given doesn't match expected amount based on totalkwh and kwhprice"
            )
            return JSONResponse(status_code=400, content=error)
        
        # -------------------------------------
        # input data is valid
        # let's check if the reservation exists
        # -------------------------------------        

        # find a reservation that matches the input
        # and hasn't been labeled as "charging / has charged"
        cursor.execute("""
            SELECT reservationid, has_charged
            FROM reservation 
            WHERE pointid = %s
                AND reservationtime <= %s
                AND reservationexpiry >= %s
                AND has_charged = 0
                AND sessionid IS NULL
            ORDER BY reservationtime DESC
            LIMIT 1
        """, (session_data.pointid, start_dt, end_dt))
        
        reservation = cursor.fetchone()
        
        # did we find a matching reservation?
        if not reservation:
            error = build_error_log(
                request, 400, "Bad request",
                "Either a reservation that matches the input doesn't exist or it's already began" 
            )
            return JSONResponse(status_code=400, content=error)

        # ------------------------------------------------------
        # a matching reservation exists, let's update our tables
        # ------------------------------------------------------
        
        # insert session
        cursor.execute("""
            INSERT INTO sessions 
            (starttime, endtime, startsoc, endsoc, totalkwh, kwprice, amount, pointid) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            start_dt,
            end_dt,
            session_data.startsoc,
            session_data.endsoc,
            session_data.totalkwh,
            session_data.kwhprice,
            session_data.amount,
            session_data.pointid
        ))
        session_id = cursor.lastrowid   # session_id is AUTO INCREMENT
        
        # update reservations
        cursor.execute("""
            UPDATE reservation 
            SET has_charged = 1, 
                sessionid = %s
            WHERE reservationid = %s
        """, (session_id, reservation['reservationid']))
        
        # we record sessions after they're done
        # reset outlet to available
        cursor.execute("""
            UPDATE outlet 
            SET state = 'available' 
            WHERE outletid = %s
                AND state IN ('charging', 'reserved')
        """, (session_data.pointid,))
        conn.commit()

        # success response
        return JSONResponse(status_code=200, content={})
            
    except mysql.connector.Error as db_error:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        error = build_error_log(
            request, 400, "Database error",
            str(db_error)
        )
        return JSONResponse(status_code=400, content=error)
        
    except Exception as e:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        error = build_error_log(
            request, 500, "Internal server error",
            str(e)
        )
        return JSONResponse(status_code=500, content=error)
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()