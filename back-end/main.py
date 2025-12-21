from fastapi import FastAPI


from management.healthcheck import router as healthcheck_router
from management.restpoints import router as restpoints_router
from management.addpoints import router as addpoints_router


app = FastAPI()


app.include_router(healthcheck_router)
app.include_router(restpoints_router)
app.include_router(addpoints_router)


@app.get("/")
def root():
    return {"message": "EV Charging API"}