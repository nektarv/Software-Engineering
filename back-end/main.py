from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from management.healthcheck import router as healthcheck_router
from management.resetpoints import router as restpoints_router
from management.addpoints import router as addpoints_router

from endpoints.points import router as points_router
from endpoints.reservePoint import router as reservePoint_router
from endpoints.updPoint import router as updPoint_router
from endpoints.newSession import router as newSession_router
from endpoints.sessions import router as sessions_router
from endpoints.pointstatus import router as pointstatus_router
from endpoints.authentication import router as auth_router
#from endpoints.authentication_v2 import router as auth_router_v2 # will probably remove
from endpoints.userStats import router as userStats_router
from endpoints.chargers import router as chargers_router
from endpoints.favorites import router as favorites_router
#for reservation
from endpoints.cleanup_reservation import router as cleanup_reservation_router
#for map
from endpoints.station import router as station_router


from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from utils import build_error_log  # adjust import path
from fastapi import FastAPI



app = FastAPI()

# management
app.include_router(healthcheck_router)
app.include_router(restpoints_router)
app.include_router(addpoints_router)

# authentication
app.include_router(auth_router)
#app.include_router(auth_router_v2) # will probably remove

# main endpoints
app.include_router(points_router)
app.include_router(reservePoint_router)
app.include_router(updPoint_router)
app.include_router(newSession_router)
app.include_router(sessions_router)
app.include_router(pointstatus_router)

# use cases
app.include_router(userStats_router)
app.include_router(chargers_router)
app.include_router(favorites_router)
app.include_router(cleanup_reservation_router)
app.include_router(station_router)



def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="EV Charging API",
        version="1.0.0",
        description="API for electric vehicle charging stations",
        routes=app.routes,
    )
    
    # force HTTPS in Swagger UI
    openapi_schema["servers"] = [
        {
            "url": "https://localhost:9876",
            "description": "Local HTTPS server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "EV Charging API"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = build_error_log(request, 400, "Bad request", str(exc))
    return JSONResponse(status_code=400, content=payload)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=9876,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        reload=True
    )