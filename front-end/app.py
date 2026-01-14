from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

FASTAPI_BACKEND_URL = "http://127.0.0.1:9876"

@app.get("/", response_class=HTMLResponse)
@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    # Fetch chargers from FastAPI backend
    # response = requests.get(f"{FASTAPI_BACKEND_URL}/api/chargers")
    # chargers = response.json()
    # map_html = generate_map(chargers)  # Optional Folium integration

    return templates.TemplateResponse("map.html", {
        "request": request,
        "active_page": "map",
        # "map_html": map_html,
        # "chargers": chargers
    })

@app.get("/list", response_class=HTMLResponse)
async def list_page(request: Request):
    # response = requests.get(f"{FASTAPI_BACKEND_URL}/api/chargers")
    # chargers = response.json()
    return templates.TemplateResponse("list.html", {
        "request": request,
        "active_page": "list",
        # "chargers": chargers
    })

@app.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request):
    return templates.TemplateResponse("stats.html", {
        "request": request,
        "active_page": "stats"
    })
