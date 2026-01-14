from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

#  change this back to "https://127.0.0.1:9876" when everything figured out 
FASTAPI_BACKEND_URL = "http://localhost:9876"
VERIFY_TLS = True


def _backend_get(path: str, params: dict):
    return requests.get(
        f"{FASTAPI_BACKEND_URL}{path}",
        params=params,
        timeout=10,
        verify=VERIFY_TLS,
    )


def _backend_post(path: str):
    return requests.post(
        f"{FASTAPI_BACKEND_URL}{path}",
        timeout=10,
        verify=VERIFY_TLS,
    )


def _backend_delete(path: str):
    return requests.delete(
        f"{FASTAPI_BACKEND_URL}{path}",
        timeout=10,
        verify=VERIFY_TLS,
    )


def _redirect_back(request: Request, fallback: str = "/list"):
    referer = request.headers.get("referer")
    return RedirectResponse(url=referer or fallback, status_code=303)


@app.get("/", response_class=HTMLResponse, name="map_page")
@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):

    # Fetch chargers from FastAPI backend
    response = requests.get(f"{FASTAPI_BACKEND_URL}/api/points")
    chargers = response.json()
    # map_html = generate_map(chargers)  # Optional Folium integration

    return templates.TemplateResponse("map.html", {
        "request": request,
        "active_page": "map",
        # "map_html": map_html,
         "chargers": chargers
    })


def _to_float_or_none(x):
    if x is None:
        return None
    if isinstance(x, str) and x.strip() == "":
        return None
    try:
        return float(x)
    except Exception:
        return None


def _to_int_or_none(x):
    if x is None:
        return None
    if isinstance(x, str) and x.strip() == "":
        return None
    try:
        return int(x)
    except Exception:
        return None

@app.get("/list", response_class=HTMLResponse, name="list_page")
async def list_page(
    request: Request,
    min_price: str | None = None,
    max_price: str | None = None,
    location_q: str | None = None,
    connector: str | None = None,
    min_power: str | None = None,
    max_power: str | None = None,
    price_time: str | None = None,
    favourites_only: int = 0,
):
    min_price_f = _to_float_or_none(min_price)
    max_price_f = _to_float_or_none(max_price)
    min_power_i = _to_int_or_none(min_power)
    max_power_i = _to_int_or_none(max_power)

    # userid comes from cookie (placeholder "login")
    userid_cookie = request.cookies.get("userid")
    userid_i = None
    try:
        if userid_cookie:
            userid_i = int(userid_cookie)
    except Exception:
        userid_i = None

    # If user not logged in and asked for favourites-only → show warning and treat as off
    warning = None
    effective_favourites_only = favourites_only
    if favourites_only == 1 and userid_i is None:
        warning = "You need to be logged in to view favourites."
        effective_favourites_only = 0  # prevent backend 400

    params = {
        "format": "json",
        "favourites_only": effective_favourites_only,
    }
    if min_price_f is not None: params["min_price"] = min_price_f
    if max_price_f is not None: params["max_price"] = max_price_f
    if location_q: params["location_q"] = location_q
    if connector: params["connector"] = connector
    if min_power_i is not None: params["min_power"] = min_power_i
    if max_power_i is not None: params["max_power"] = max_power_i
    if price_time: params["price_time"] = price_time
    if userid_i is not None: params["userid"] = userid_i

    chargers = []
    api_error = None
    api_error_details = None

    try:
        r = _backend_get("/api/chargers", params=params)
        if r.status_code == 204:
            chargers = []
        elif r.status_code == 200:
            chargers = r.json()
        else:
            api_error = f"Backend error ({r.status_code})"
            try:
                api_error_details = r.json()
            except Exception:
                api_error_details = {"raw": r.text}
    except Exception as e:
        api_error = "Network error"
        api_error_details = {"raw": str(e)}

    filters = {
        "min_price": "" if min_price_f is None else str(min_price_f),
        "max_price": "" if max_price_f is None else str(max_price_f),
        "location_q": location_q or "",
        "connector": connector or "",
        "min_power": "" if min_power_i is None else str(min_power_i),
        "max_power": "" if max_power_i is None else str(max_power_i),
        "price_time": price_time or "",
        "favourites_only": favourites_only,
    }

    return templates.TemplateResponse(
        "list.html",
        {
            "request": request,
            "active_page": "list",
            "chargers": chargers,
            "filters": filters,
            "api_error": api_error,
            "api_error_details": api_error_details,
            "warning": warning,
            "is_logged_in": userid_i is not None,
            "userid": userid_i,
        },
    )



@app.post("/favourites/add")
async def favourites_add(request: Request, stationid: int = Form(...)):
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        return RedirectResponse(url="/login", status_code=303)
    try:
        userid_i = int(userid_cookie)
        _backend_post(f"/api/favourites/{userid_i}/{stationid}")
    except Exception:
        pass
    return _redirect_back(request, fallback="/list")


@app.post("/favourites/remove")
async def favourites_remove(
    request: Request,
    userid: int = Form(...),
    stationid: int = Form(...),
):
    try:
        _backend_delete(f"/api/favourites/{userid}/{stationid}")
    except Exception:
        pass
    return _redirect_back(request, fallback="/list")


@app.get("/stats", response_class=HTMLResponse, name="stats_page")
async def stats_page(request: Request):
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "active_page": "stats",
        },
    )

@app.get("/login", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})



@app.post("/login")
async def login_submit(request: Request, userid: int = Form(...)):
    resp = RedirectResponse(url="/list", status_code=303)
    resp.set_cookie("userid", str(userid), httponly=True)
    return resp

@app.post("/logout")
async def logout():
    resp = RedirectResponse(url="/list", status_code=303)
    resp.delete_cookie("userid")
    return resp




