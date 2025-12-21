from fastapi import FastAPI
import mysql.connector


# db settings
DB_CONFIG = {
    "host": "localhost",
    "user": "root",          
    "password": "ElectroWay",
    "database": "charging_database",
}


from management.healthcheck import router as healthcheck_router


app = FastAPI()


app.include_router(healthcheck_router)


@app.get("/")
def root():
    return {"message": "EV Charging API"}