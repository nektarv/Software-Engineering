# backend/endpoints/cleanup_reservation.py
from fastapi import APIRouter, Request
import mysql.connector
from utils import DB_CONFIG

router = APIRouter(prefix="/api", tags=["cleanup"])

@router.get("/cleanup-reservation")
def cleanup_reservations():
    """
    Αποδεσμεύει αυτόματα τους φορτιστές των οποίων η κράτηση έχει λήξει.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # SQL Query που ενημερώνει το status σε 'available' 
        # αν η τρέχουσα ώρα είναι μεγαλύτερη από την ώρα λήξης (reservationexpiry)
        sql_update = """
            UPDATE outlet 
            SET state = 'available' 
            WHERE state = 'reserved' AND outletid IN (
                SELECT pointid FROM reservation WHERE reservationexpiry < NOW()
            )
        """
        cur.execute(sql_update)
        updated_count = cur.rowcount # Πόσες γραμμές άλλαξαν
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "success", "cleared_chargers": updated_count}
    except Exception as e:
        return {"status": "error", "message": str(e)}