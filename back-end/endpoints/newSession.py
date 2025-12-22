from datetime import datetime
from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
import mysql.connector
from pydantic import BaseModel
from typing import Optional

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

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
    """
    (e) POST /api/newsession
    Log a completed charging session.
    Requires a reservation that satisfies the session.
    """
    
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        try:
            start_dt = datetime.strptime(session_data.starttime, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(session_data.endtime, "%Y-%m-%d %H:%M")
        except ValueError:
            error = build_error_log(
                request, 400, "Bad request",
                "Invalid time format. Use: YYYY-MM-DD HH:MM"
            )
            return JSONResponse(status_code=400, content=error)
        
        if end_dt <= start_dt:
            error = build_error_log(
                request, 400, "Bad request",
                "endtime must be after starttime"
            )
            return JSONResponse(status_code=400, content=error)
        
        if not (0 <= session_data.startsoc <= 100):
            error = build_error_log(
                request, 400, "Bad request",
                "startsoc must be between 0 and 100"
            )
            return JSONResponse(status_code=400, content=error)
        
        if not (0 <= session_data.endsoc <= 100):
            error = build_error_log(
                request, 400, "Bad request",
                "endsoc must be between 0 and 100"
            )
            return JSONResponse(status_code=400, content=error)
        
        if session_data.endsoc <= session_data.startsoc:
            error = build_error_log(
                request, 400, "Bad request",
                "endsoc must be greater than startsoc"
            )
            return JSONResponse(status_code=400, content=error)
        
        expected_amount = session_data.totalkwh * session_data.kwhprice
        if abs(session_data.amount - expected_amount) > 0.001: # allow rounding differences
            error = build_error_log(
                request, 400, "Bad request",
                f"amount ({session_data.amount}) doesn't match totalkwh × kwhprice ({expected_amount:.2f})"
            )
            return JSONResponse(status_code=400, content=error)
        
        if session_data.totalkwh <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "totalkwh must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        if session_data.kwhprice <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "kwhprice must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        if session_data.amount <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "amount must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        cursor.execute("SELECT * FROM outlet WHERE outletid = %s", (session_data.pointid,))
        point = cursor.fetchone()
        
        if not point:
            error = build_error_log(
                request, 404, "Not found",
                f"Point {session_data.pointid} does not exist"
            )
            return JSONResponse(status_code=404, content=error)
        
        # find matching reservation
        cursor.execute("""
            SELECT reservationid, has_charged
            FROM reservation 
            WHERE pointid = %s
              AND reservationtime <= %s
              AND reservationexpiry >= %s
              AND has_charged = 0
            ORDER BY reservationtime DESC
            LIMIT 1
        """, (session_data.pointid, start_dt, end_dt))
        
        reservation = cursor.fetchone()
        
        if not reservation:
            error = build_error_log(
                request, 400, "Bad request",
                "No active reservation found for this point and time period"
            )
            return JSONResponse(status_code=400, content=error)
        
        if reservation['has_charged'] == 1:
            error = build_error_log(
                request, 400, "Bad request",
                "Reservation already has a charging session"
            )
            return JSONResponse(status_code=400, content=error)
        
        cursor.execute("""
            INSERT INTO sessions 
            (pointid, starttime, endtime, startsoc, endsoc, totalkwh, kwprice, amount) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            session_data.pointid,
            start_dt,
            end_dt,
            session_data.startsoc,
            session_data.endsoc,
            session_data.totalkwh,
            session_data.kwhprice,
            session_data.amount
        ))
        
        session_id = cursor.lastrowid
        
        cursor.execute("""
            UPDATE reservation 
            SET has_charged = 1, 
                sessionid = %s
            WHERE reservationid = %s
        """, (session_id, reservation['reservationid']))
        
        cursor.execute("""
            UPDATE outlet 
            SET state = 'available' 
            WHERE outletid = %s
        """, (session_data.pointid,))
        
        conn.commit()

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