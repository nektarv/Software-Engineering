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

app = FastAPI()

app.include_router(healthcheck_router)
app.include_router(restpoints_router)
app.include_router(addpoints_router)

app.include_router(points_router)
app.include_router(reservePoint_router)
app.include_router(updPoint_router)
app.include_router(newSession_router)
app.include_router(sessions_router)
app.include_router(pointstatus_router)

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
            "url": "https://localhost:9876",  # force HTTPS
            "description": "Local HTTPS server"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "EV Charging API"}

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