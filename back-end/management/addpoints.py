from datetime import datetime
from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import JSONResponse
import mysql.connector
import csv, io

from utils import DB_CONFIG, build_error_log


def get_or_create_station(cursor, address, lat, lon, name, provider):
    
    cursor.execute(
      """
      SELECT stationid FROM station
      WHERE address = %s
       AND Latitude = %s
       AND Longitude = %s
       AND name = %s
       AND provider = %s
      """,
      (address, lat, lon, name, provider)
    )

    station = cursor.fetchone()

    if station:
      return station[0] #the station exists

    cursor.execute(
      """
      INSERT INTO station (address, Latitude, Longitude, name, provider)
      VALUES (%s, %s, %s, %s, %s)
      """,
      (address, lat, lon, name, provider)
    )
    return cursor.lastrowid


router = APIRouter()


@router.post("/admin/addpoints")
async def admin_addpoints(request: Request, file: UploadFile = File(...)):

  if file.content_type != "text/csv":
    error_body = build_error_log(
      request=request,
      code = 400,
      error_text = "Wrong file type",
      raw_debuginfo = f"got {file.content_type} and expected text/csv"
    )
    return JSONResponse(status_code=400, content=error_body)

  # read the file in bytes
  contents = await file.read()
  # convert bytes in text 
  text = contents.decode("utf-8")
  # csv reader (expects header)
  reader = csv.DictReader(io.StringIO(text))

  try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for row in reader:
          address   = row["address"]
          lat       = float(row["Latitude"])
          lon       = float(row["Longitude"])
          name      = row["station_name"]
          provider  = row["provider"]
          connector = row["connector"]
          power     = int(row["power"])
          state     = row["state"]
          is_fast   = int(row["is_fast"])
          markup    = float(row["markup"])

          stationid = get_or_create_station(
                cursor,
                address=address,
                lat=lat,
                lon=lon,
                name=name,
                provider=provider,
            )

          cursor.execute(
            """
              INSERT INTO outlet (connector, power, state, is_fast, markup, stationid)
              VALUES (%s, %s, %s, %s, %s, %s)
              """,
              (connector, power, state, is_fast, markup, stationid)
          )

    conn.commit()
    cursor.close()
    conn.close()

  except Exception as e:
        error_body = build_error_log(
            request=request,
            code=500,
            error_text="Error in /admin/addpoints",
            raw_debuginfo=str(e)
        )
        return JSONResponse(status_code=500, content=error_body)

  return {"status": "OK"}
