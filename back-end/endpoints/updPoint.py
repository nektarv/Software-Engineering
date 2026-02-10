from fastapi import APIRouter, Request, Path, Body
from fastapi.responses import JSONResponse
import mysql.connector
from pydantic import BaseModel
from typing import Optional

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["points"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}

class UpdatePointRequest(BaseModel):
    status: Optional[str] = None
    kwhprice: Optional[float] = None

@router.post("/updpoint/{point_id}")
async def update_point(
    point_id: int = Path(..., ge=1),
    update_data: UpdatePointRequest = Body(...),
    request: Request = None
):
    conn = None
    cursor = None    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True, buffered=True)
        
        cursor.execute("SELECT * FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()
        
        # if point doesn't exist, return 404
        if not point:
            error = build_error_log(
                request, 404, "Not found",
                f"Charging point {point_id} does not exist"
            )
            return JSONResponse(status_code=404, content=error)
        
        # at least one field must be provided
        if update_data.status is None and update_data.kwhprice is None:
            error = build_error_log(
                request, 400, "Bad request", 
                "At least one of 'status' and 'kwh price' must be provided"
            )
            return JSONResponse(status_code=400, content=error)
        
        # check if status is one of allowed values
        if update_data.status and update_data.status not in ALLOWED_STATUSES:
            error = build_error_log(
                request, 400, "Bad request",
                "Invalid status"
            )
            return JSONResponse(status_code=400, content=error)
        
        # check if price is valid
        if update_data.kwhprice is not None and update_data.kwhprice <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "kWh price must be a positive number"
            )
            return JSONResponse(status_code=400, content=error)
        
        updates = []    # stores columns to be updated
        values = []     # stores values of columns to be updated
        
        # if user requested to change status, add it to our data
        if update_data.status:
            updates.append("state = %s")
            values.append(update_data.status)

        # find most recent valid dam value
        cursor.execute("""
            SELECT price_eur_per_kwh 
            FROM dam_prices 
            WHERE price_eur_per_kwh IS NOT NULL 
            ORDER BY timeref DESC 
            LIMIT 1
        """)
        dam = cursor.fetchone()

        # if user requested to change kwh_price, compute new markup
        if update_data.kwhprice is not None:
            new_markup = float(update_data.kwhprice) / float(dam['price_eur_per_kwh'])
            updates.append("markup = %s")
            values.append(new_markup)
        
        # update outlet table with new values, where outletid=point_id
        if updates:
            values.append(point_id)
            query = f"UPDATE outlet SET {', '.join(updates)} WHERE outletid = %s"
            cursor.execute(query, values)
            conn.commit()
        
        # read back the results to return exactly what the database has
        cursor.execute(
            "SELECT outletid, state, markup FROM outlet WHERE outletid = %s",
            (point_id,)
        )
        updated_point = cursor.fetchone()

        if updated_point['markup'] is None:
            kwh_price = None
        else:
            final_price = float(dam['price_eur_per_kwh']) * float(updated_point['markup'])
            kwh_price = round(final_price, 4)

        # success response
        return {
            "pointid": point_id,
            "status": updated_point['state'],
            "kwhprice": kwh_price
        }
        
    except mysql.connector.Error as db_error:
        error = build_error_log(
            request, 400, "Database error",
            str(db_error)
        )
        return JSONResponse(status_code=400, content=error)
        
    except Exception as e:
        error = build_error_log(
            request, 500, "Internal server error",
            str(e)
        )
        return JSONResponse(status_code=500, content=error)
        
    finally:
        if cursor:
            cursor.close()
        if conn is not None and conn.is_connected():
            conn.close()