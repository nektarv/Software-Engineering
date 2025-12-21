from fastapi import FastAPI


from management.healthcheck import router as healthcheck_router
from management.restpoints import router as restpoints_router
from management.addpoints import router as addpoints_router

from functional.points import router as points_router
from functional.sessions import router as sessions_router
from functional.pointstatus import router as pointstatus_router
from functional.updPoint import router as updPoint_router

app = FastAPI()

app.include_router(healthcheck_router)
app.include_router(restpoints_router)
app.include_router(addpoints_router)

app.include_router(points_router)
app.include_router(updPoint_router)
app.include_router(sessions_router)
app.include_router(pointstatus_router)

@app.get("/")
def root():
    return {"message": "EV Charging API"}