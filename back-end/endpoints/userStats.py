# user_stats.py
from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import mysql.connector
from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api/user", tags=["statistics"])

@router.get("/statistics")
async def get_user_statistics(
    request: Request,
    userid: int = Query(..., description="User ID"),
    minutes: int = Query(..., description="Time range in minutes")
):
    conn = None
    cursor = None
    
    try:
        # check if minutes are positive
        # frontend will enforce specific time ranges via dropdown menu
        if minutes <= 0:
            error = build_error_log(
                request, 400, "Bad request",
                "Minutes parameter must be positive"
            )
            return JSONResponse(status_code=400, content=error)
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # check if user id is valid
        cursor.execute(
            "SELECT userid FROM users WHERE userid = %s",
            (userid,)
        )
        user_exists = cursor.fetchone()
        
        if not user_exists:
            error = build_error_log(
                request, 400, "Bad request",
                f"User with ID {userid} does not exist"
            )
            return JSONResponse(status_code=400, content=error)
        
        # date range
        to_date = datetime.now()
        from_date = to_date - timedelta(minutes=minutes)
        
        # summarize stats
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT s.sessionid) as total_sessions,
                SUM(TIMESTAMPDIFF(MINUTE, s.starttime, s.endtime)) as total_charging_time_minutes,
                SUM(s.amount) as total_cost_eur,
                SUM(s.totalkwh) as total_energy_kwh,
                CASE 
                    WHEN COUNT(DISTINCT s.sessionid) > 0 
                    THEN SUM(s.amount) / COUNT(DISTINCT s.sessionid)
                    ELSE 0 
                END as avg_cost_per_session,
                CASE 
                    WHEN COUNT(DISTINCT s.sessionid) > 0 
                    THEN SUM(s.totalkwh) / COUNT(DISTINCT s.sessionid)
                    ELSE 0 
                END as avg_energy_per_session
            FROM sessions s
            JOIN reservation r ON s.sessionid = r.sessionid
            WHERE r.userid = %s
                AND s.starttime >= %s
                AND s.endtime <= %s
        """, (userid, from_date, to_date))
        
        summary_result = cursor.fetchone()
        
        # top chargers
        cursor.execute("""
            SELECT 
                st.stationid,
                st.name as station_name,
                st.Latitude,
                st.Longitude,
                o.connector as connector_type,
                COUNT(*) as usage_count,
                SUM(s.totalkwh) as total_energy_kwh,
                SUM(s.amount) as total_cost_eur,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM favourites f 
                        WHERE f.userid = %s AND f.stationid = st.stationid
                    ) THEN TRUE
                    ELSE FALSE
                END as is_favorite
            FROM sessions s
            JOIN reservation r ON s.sessionid = r.sessionid
            JOIN outlet o ON s.pointid = o.outletid
            JOIN station st ON o.stationid = st.stationid
            WHERE r.userid = %s
                AND s.starttime >= %s
                AND s.endtime <= %s
            GROUP BY st.stationid, st.name, st.Latitude, st.Longitude, o.connector
            ORDER BY usage_count DESC
            LIMIT 5
        """, (userid, userid, from_date, to_date))
        
        top_chargers = cursor.fetchall()
        
        # cost over time chart
        cursor.execute("""
            SELECT 
                DATE(s.starttime) as period,
                SUM(s.amount) as total_cost
            FROM sessions s
            JOIN reservation r ON s.sessionid = r.sessionid
            WHERE r.userid = %s
                AND s.starttime >= %s
                AND s.endtime <= %s
            GROUP BY DATE(s.starttime)
            ORDER BY period
        """, (userid, from_date, to_date))
        
        cost_over_time = cursor.fetchall()
        
        # energy over time chart
        cursor.execute("""
            SELECT 
                DATE(s.starttime) as period,
                SUM(s.totalkwh) as total_energy
            FROM sessions s
            JOIN reservation r ON s.sessionid = r.sessionid
            WHERE r.userid = %s
                AND s.starttime >= %s
                AND s.endtime <= %s
            GROUP BY DATE(s.starttime)
            ORDER BY period
        """, (userid, from_date, to_date))
        
        energy_over_time = cursor.fetchall()
        
        # location breakdown for pie chart
        cursor.execute("""
            SELECT 
                st.stationid,
                st.name as station_name,
                SUM(TIMESTAMPDIFF(MINUTE, s.starttime, s.endtime)) as charging_minutes,
                SUM(s.totalkwh) as total_energy_kwh,
                SUM(s.amount) as total_cost_eur
            FROM sessions s
            JOIN reservation r ON s.sessionid = r.sessionid
            JOIN outlet o ON s.pointid = o.outletid
            JOIN station st ON o.stationid = st.stationid
            WHERE r.userid = %s
                AND s.starttime >= %s
                AND s.endtime <= %s
            GROUP BY st.stationid, st.name
            ORDER BY charging_minutes DESC
        """, (userid, from_date, to_date))
        
        location_data = cursor.fetchall()
        
        # calculate percentages for pie chart
        total_minutes = sum(loc['charging_minutes'] or 0 for loc in location_data)
        for loc in location_data:
            loc['percentage'] = round((loc['charging_minutes'] / total_minutes * 100), 2) if total_minutes > 0 else 0

        # format response
        response = {
            "userid": userid,
            "minutes": minutes,
            "period": {
                "from": from_date.strftime("%Y-%m-%d %H:%M:%S"),
                "to": to_date.strftime("%Y-%m-%d %H:%M:%S")
            },
            "summary": {
                "total_sessions": summary_result['total_sessions'] or 0,
                "total_charging_time_minutes": summary_result['total_charging_time_minutes'] or 0,
                "total_cost_eur": float(summary_result['total_cost_eur'] or 0),
                "total_energy_kwh": float(summary_result['total_energy_kwh'] or 0),
                "avg_cost_per_session": float(summary_result['avg_cost_per_session'] or 0),
                "avg_energy_per_session": float(summary_result['avg_energy_per_session'] or 0)
            },
            "top_chargers": top_chargers,
            "cost_over_time": cost_over_time,
            "energy_over_time": energy_over_time,
            "location_breakdown": location_data
        }
        
        return response
        
    except mysql.connector.Error as db_error:
        error = build_error_log(
            request, 400, "Bad request",
            f"Database error: {str(db_error)}"
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