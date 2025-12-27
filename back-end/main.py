from fastapi import FastAPI

from management.healthcheck import router as healthcheck_router
from management.resetpoints import router as restpoints_router
from management.addpoints import router as addpoints_router

from endpoints.points import router as points_router
from endpoints.reservePoint import router as reservePoint_router
from endpoints.updPoint import router as updPoint_router
from endpoints.newSession import router as newSession_router
from endpoints.sessions import router as sessions_router
from endpoints.pointstatus import router as pointstatus_router

app = FastAPI(openapi_prefix="/api")

app.include_router(healthcheck_router)
app.include_router(restpoints_router)
app.include_router(addpoints_router)

app.include_router(points_router)
app.include_router(reservePoint_router)
app.include_router(updPoint_router)
app.include_router(newSession_router)
app.include_router(sessions_router)
app.include_router(pointstatus_router)

@app.get("/")
def root():
    return {"message": "EV Charging API"}