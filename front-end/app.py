from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

FASTAPI_BACKEND_URL = "https://localhost:9876"
VERIFY_SSL = False # need it false for self-signed certificates

def _backend_get(path: str, params: dict = None):
    return requests.get(
        f"{FASTAPI_BACKEND_URL}{path}",
        params=params,
        timeout=10,
        verify=VERIFY_SSL,
    )

def _backend_post(path: str, json_data: dict = None):
    return requests.post(
        f"{FASTAPI_BACKEND_URL}{path}",
        json=json_data,
        timeout=10,
        verify=VERIFY_SSL,
    )

def _backend_delete(path: str):
    return requests.delete(
        f"{FASTAPI_BACKEND_URL}{path}",
        timeout=10,
        verify=VERIFY_SSL,
    )

def _redirect_back(request: Request, fallback: str = "/list"):
    referer = request.headers.get("referer")
    return RedirectResponse(url=referer or fallback, status_code=303)

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

@app.get("/fetch-charger/{pointid}")
def fetch_charger(pointid: str):
    """Experimental endpoint - fetch single charger"""
    backend_url = f"{FASTAPI_BACKEND_URL}/api/point/{pointid}"
    response = requests.get(backend_url, verify=VERIFY_SSL)
    return response.json()

@app.get("/", response_class=HTMLResponse, name="map_page")
@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):
    """Homepage with charger map - MUST WORK WITHOUT LOGIN"""
    userid = request.cookies.get("userid")
    username = request.cookies.get("username")
    
    chargers = []
    backend_error = None
    
    try:
        response = _backend_get("/api/points")
        if response.status_code == 200:
            chargers = response.json()
        else:
            backend_error = f"Backend returned {response.status_code}"
    except Exception as e:
        backend_error = f"Cannot load chargers: {str(e)}"

    return templates.TemplateResponse("map.html", {
        "request": request,
        "active_page": "map",
        "chargers": chargers,
        "backend_url": FASTAPI_BACKEND_URL,
        "is_logged_in": userid is not None,
        "username": username,
        "userid": userid,
        "backend_error": backend_error
    })

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
    """Charger listing page with filters"""
    min_price_f = _to_float_or_none(min_price)
    max_price_f = _to_float_or_none(max_price)
    min_power_i = _to_int_or_none(min_power)
    max_power_i = _to_int_or_none(max_power)

    userid_cookie = request.cookies.get("userid")
    username_cookie = request.cookies.get("username")
    userid_i = None
    try:
        if userid_cookie:
            userid_i = int(userid_cookie)
    except Exception:
        userid_i = None

    warning = None
    effective_favourites_only = favourites_only
    if favourites_only == 1 and userid_i is None:
        warning = "You need to be logged in to view favourites."
        effective_favourites_only = 0

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
            "username": username_cookie,
            "userid": userid_i,
        },
    )

@app.post("/favourites/add")
async def favourites_add(request: Request, stationid: int = Form(...)):
    """Add charger to favourites"""
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        return RedirectResponse(url="/authentication", status_code=303)
    
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
    """Remove charger from favourites"""
    try:
        _backend_delete(f"/api/favourites/{userid}/{stationid}")
    except Exception:
        pass
    
    return _redirect_back(request, fallback="/list")

@app.get("/stats", response_class=HTMLResponse, name="stats_page")
async def stats_page(request: Request):
    """Statistics page"""
    userid = request.cookies.get("userid")
    username = request.cookies.get("username")
    
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "active_page": "stats",
            "is_logged_in": userid is not None,
            "username": username,
            "userid": userid
        },
    )

@app.get("/authentication", response_class=HTMLResponse, name="login_page")
async def login_page(request: Request, error: str = None):
    """Authentication page"""
    return templates.TemplateResponse(
        "authentication.html", 
        {
            "request": request,
            "error": error
        }
    )

@app.post("/authentication")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle authentication form submission"""
    try:
        auth_response = _backend_post(
            "/api/authentication/authentication",
            json_data={"username": username, "password": password}
        )
        
        backend_status = auth_response.status_code
        
        if backend_status == 200:
            # Authentication successful
            user_data = auth_response.json()
            
            # Redirect to map page with cookies
            response = RedirectResponse(url="/map", status_code=303)
            response.set_cookie("userid", str(user_data["userid"]), httponly=True)
            response.set_cookie("username", user_data["username"], httponly=True)
            return response
            
        else:
            # Authentication failed
            try:
                error_data = auth_response.json()
                error_msg = error_data.get("error", "Authentication failed")
            except:
                error_msg = "Invalid username or password"
            
            # Return to authentication page with error
            return templates.TemplateResponse(
                "authentication.html",
                {
                    "request": request,
                    "error": f"Error {backend_status}: {error_msg}"
                },
                status_code=backend_status
            )
            
    except requests.exceptions.ConnectionError:
        # Cannot connect to backend
        return templates.TemplateResponse(
            "authentication.html",
            {
                "request": request,
                "error": "Cannot connect to authentication server"
            },
            status_code=500
        )

@app.post("/logout")
async def logout():
    """Logout user - clear all authentication cookies"""
    resp = RedirectResponse(url="/", status_code=303)
    resp.delete_cookie("userid")
    resp.delete_cookie("username")
    return resp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem",
        reload=True
    )