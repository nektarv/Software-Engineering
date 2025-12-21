from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector

from management.utils import DB_CONFIG, build_error_log


from pathlib import Path


from management.resetpoints_extractor import insert_from_json


router = APIRouter()


@router.post("/admin/resetpoints")
def admin_resetpoints(request: Request): 

  # Hardwired path - same for everyone (database directory of the project)
  JSON_FILE = Path("management/parts1234.json")

  if not JSON_FILE.exists():
      # error 400
      error_body = build_error_log(
      request=request,
      code=400,
      error_text="JSON file not found", 
      raw_debuginfo=str(JSON_FILE),
      )
      return JSONResponse(status_code=400, content=error_body)

  
  # DB Connection and Reset tables
  try:
      conn = mysql.connector.connect(**DB_CONFIG)
      cursor = conn.cursor()

      cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
      # Clear tables πριν insert
      cursor.execute("DELETE FROM sessions")
      cursor.execute("DELETE FROM reservation")
      cursor.execute("DELETE FROM updates") 
      cursor.execute("DELETE FROM favourites")
      cursor.execute("DELETE FROM outlet")
      cursor.execute("DELETE FROM station")

      cursor.execute("ALTER TABLE station AUTO_INCREMENT = 1")
      cursor.execute("ALTER TABLE outlet AUTO_INCREMENT = 1")

      conn.commit()

      cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

      # insert from JSON with the extractor
      inserted = insert_from_json(conn, cursor, JSON_FILE)

      cursor.close()
      conn.close()
        
  except Exception as e:
      error_body = build_error_log(
          request=request,
          code=500,
          error_text="Database reset failed", 
          raw_debuginfo=str(e),
      )
      return JSONResponse(status_code=500, content=error_body)

  return JSONResponse(status_code=200, content={"status": "OK", "inserted_stations": inserted})
