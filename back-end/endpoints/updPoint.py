from fastapi import APIRouter, Request, Body
from fastapi.responses import JSONResponse
import mysql.connector
from pydantic import BaseModel
from typing import Optional

from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api", tags=["functional"])

ALLOWED_STATUSES = {"available", "charging", "reserved", "malfunction", "offline"}

class UpdatePointRequest(BaseModel):
    status: Optional[str] = None
    kwhprice: Optional[float] = None

@router.post("/updpoint/{point_id}")
async def update_point(
    point_id: int,
    update_data: UpdatePointRequest = Body(...),
    request: Request = None
):
    """
    (d) POST /api/updpoint/{point_id}
    Update a charging point's status and/or price.
    """

    # at least one field must be provided
    if update_data.status is None and update_data.kwhprice is None:
        error = build_error_log(
            request, 400, "Bad request", 
            "At least one of 'status' or 'kwhprice' must be provided"
        )
        return JSONResponse(status_code=400, content=error)
    
    # check if status is one of allowed values
    if update_data.status and update_data.status not in ALLOWED_STATUSES:
        error = build_error_log(
            request, 400, "Bad request",
            f"Invalid status. Must be one of: {ALLOWED_STATUSES}"
        )
        return JSONResponse(status_code=400, content=error)
    
    # check if price is valid
    if update_data.kwhprice is not None and update_data.kwhprice <= 0:
        error = build_error_log(
            request, 400, "Bad request",
            "kwhprice must be a positive number"
        )
        return JSONResponse(status_code=400, content=error)
    
    conn = None
    cursor = None
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM outlet WHERE outletid = %s", (point_id,))
        point = cursor.fetchone()
        
        if not point:
            error = build_error_log(
                request, 404, "Not found",
                f"Point {point_id} does not exist"
            )
            return JSONResponse(status_code=404, content=error)
        
        updates = []
        values = []
        
        if update_data.status:
            updates.append("state = %s")
            values.append(update_data.status)
        
        if update_data.kwhprice is not None:
            cursor.execute(
                "SELECT price_eur_per_kwh FROM dam_prices ORDER BY timeref DESC LIMIT 1"
            )
            dam = cursor.fetchone()
            
            if not dam or dam['price_eur_per_kwh'] is None:
                error = build_error_log(
                    request, 400, "Bad request",
                    "No electricity price available (dam_prices table is empty)"
                )
                return JSONResponse(status_code=400, content=error)
            
            new_markup = float(update_data.kwhprice) / float(dam['price_eur_per_kwh'])
            updates.append("markup = %s")
            values.append(new_markup)
        
        if updates:
            values.append(point_id)
            query = f"UPDATE outlet SET {', '.join(updates)} WHERE outletid = %s"
            cursor.execute(query, values)
            conn.commit()
        
        cursor.execute(
            "SELECT outletid, state, markup FROM outlet WHERE outletid = %s",
            (point_id,)
        )
        updated_point = cursor.fetchone()
        
        cursor.execute(
            "SELECT price_eur_per_kwh FROM dam_prices ORDER BY timeref DESC LIMIT 1"
        )
        dam = cursor.fetchone()
        
        if dam and dam['price_eur_per_kwh']:
            final_price = float(dam['price_eur_per_kwh']) * float(updated_point['markup'])
            kwhprice_response = round(final_price, 4)
        else:
            kwhprice_response = None
        
        # success response
        return {
            "pointid": point_id,
            "status": updated_point['state'],
            "kwhprice": kwhprice_response
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
        if conn and conn.is_connected():
            conn.close()