from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import requests
import urllib3

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




#
#
# αυτο πλεον καλει το point-details που προστεθηκε στο αρχειο points.py 
# για να παρει και την διευθυνση
#
#
# Experimental
@app.get("/fetch-charger/{pointid}")
def fetch_charger(request: Request, pointid: str):
    # Παίρνουμε το userid από το cookie
    userid_cookie = request.cookies.get("userid")
    
    # Το στέλνουμε στο backend ως παράμετρο
    params = {}
    if userid_cookie:
        params["user_id"] = userid_cookie

    # Καλούμε το point-details
    backend_url = f"{FASTAPI_BACKEND_URL}/api/point-details/{pointid}"
    
    response = requests.get(backend_url, params=params, verify=VERIFY_SSL)
    return response.json()
# Experimental over

@app.get("/", response_class=HTMLResponse, name="map_page")
@app.get("/map", response_class=HTMLResponse)
async def map_page(request: Request):

    #TRIGGER CLEANUP: Λέμε στο backend να ελευθερώσει όσους έληξαν
    try:
        
        _backend_get("/api/cleanup-reservation")
    except Exception as e:
        print(f"Cleanup failed: {e}")

    #FETCH POINTS
    response = requests.get(f"{FASTAPI_BACKEND_URL}/api/points", verify=VERIFY_SSL)
    chargers = response.json()

    # COOKIES
    userid = request.cookies.get("userid")
    username = request.cookies.get("username")

    # RENDER
    return templates.TemplateResponse("map.html", {
        "request": request,
        "active_page": "map",
        "chargers": chargers,
        "backend_url": FASTAPI_BACKEND_URL,
        "is_logged_in": userid is not None,
        "username": username,
        "userid": userid
    })


@app.post("/reserve/{pointid}")
async def reserve_proxy(request: Request, pointid: int):
    #  Έλεγχος Login
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"message": "Please login first"})

    try:
        #  Διαβάζουμε τη διάρκεια (minutes)
        body = await request.json()
        minutes = body.get("duration", 30) # Default 30 αν δεν σταλεί

        # Το endpoint είναι: POST /api/reserve/{point_id}/{minutes}
        # ΑΛΛΑ το user_id είναι Query Parameter (?user_id=...)
        
        backend_url = f"/api/reserve/{pointid}/{minutes}?user_id={userid_cookie}"
        
        # Κλήση στο Backend
        # Το _backend_post στέλνει json=None επειδή δεν χρειάζεται body, 
        # όλα τα δεδομένα είναι στο URL.
        response = _backend_post(backend_url) 

        if response.status_code == 200:
            return response.json()
        else:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=response.status_code, content=response.json())

    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=500, content={"message": str(e)})


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

    # userid comes from cookie
    userid_cookie = request.cookies.get("userid")
    username_cookie = request.cookies.get("username")
    userid_i = None
    try:
        if userid_cookie:
            userid_i = int(userid_cookie)
    except Exception:
        userid_i = None


    # Αν ο χρήστης ζητάει αγαπημένα και δεν είναι συνδεδεμένος τοτε Redirect
    if favourites_only == 1 and userid_i is None:
        return RedirectResponse(url="/authentication", status_code=303)

    
    warning = None
    effective_favourites_only = favourites_only


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


    # Fetch available connectors from backend
    available_connectors = []
    try:
        connectors_response = _backend_get("/api/connectors")
        if connectors_response.status_code == 200:
            available_connectors = connectors_response.json()
    except Exception:
        available_connectors = []


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
            "available_connectors": available_connectors,
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
    # Παίρνουμε το ID από το cookie
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        return RedirectResponse(url="/authentication", status_code=303)
    
    try:
        userid_i = int(userid_cookie)
        # Στέλνουμε το αίτημα στο backend
        _backend_post(f"/api/favourites/{userid_i}/{stationid}")
    except Exception:
        pass # Αγνοούμε τα errors για να μην κρασάρει η σελίδα
    
    # Επιστρέφουμε πίσω στη λίστα (Reload)
    return _redirect_back(request, fallback="/list")

@app.post("/favourites/remove")
async def favourites_remove(
    request: Request,
    stationid: int = Form(...), 
):
    # Παίρνουμε το ID από το cookie (πιο ασφαλές)
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
         return _redirect_back(request, fallback="/list")

    try:
        userid_i = int(userid_cookie)
        # Στέλνουμε DELETE αίτημα στο backend
        _backend_delete(f"/api/favourites/{userid_i}/{stationid}")
    except Exception:
        pass
    
    return _redirect_back(request, fallback="/list")



# FAVOURITES (JSON BASED - ΓΙΑ ΤΟΝ ΧΑΡΤΗ)

@app.post("/favourites/add_json")
async def favourites_add_json(request: Request, stationid: int = Form(...)):
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        return JSONResponse(status_code=401, content={"message": "Login required"})
    
    try:
        userid_i = int(userid_cookie)
        # Καλούμε το backend
        resp = _backend_post(f"/api/favourites/{userid_i}/{stationid}")
        
        if resp.status_code in (200, 201):
            return {"success": True}
        else:
            return JSONResponse(status_code=resp.status_code, content={"message": "Error adding favorite"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})

@app.post("/favourites/remove_json")
async def favourites_remove_json(request: Request, stationid: int = Form(...)):
    userid_cookie = request.cookies.get("userid")
    if not userid_cookie:
        return JSONResponse(status_code=401, content={"message": "Login required"})
    
    try:
        userid_i = int(userid_cookie)
        # Καλούμε το backend (DELETE)
        resp = _backend_delete(f"/api/favourites/{userid_i}/{stationid}")
        
        if resp.status_code in (200, 204):
            return {"success": True}
        else:
            return JSONResponse(status_code=resp.status_code, content={"message": "Error removing favorite"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})





@app.get("/stats", response_class=HTMLResponse, name="stats_page")
async def stats_page(request: Request, range: int = 30):
    # 1. Παίρνουμε το userid από το cookie (όπως κάνεις και στο /list)
    userid_cookie = request.cookies.get("userid")
    username_cookie = request.cookies.get("username") 
    
    # Αν δεν είναι συνδεδεμένος, στείλτον στο login
    if not userid_cookie:
        return RedirectResponse(url="/authentication", status_code=303)
    
    try:
        userid_i = int(userid_cookie)
    except Exception:
        return RedirectResponse(url="/authentication", status_code=303)

    # 2. Μετατρέπουμε τις ημέρες (7, 30, 365) σε λεπτά για το API σου
    minutes = range * 24 * 60 

    stats_data = {}
    try:
        # 3. Καλούμε το API statistics (user_stats.py)
        # Προσοχή: Το endpoint σου είναι /api/user/statistics
        r = _backend_get("/api/user/statistics", params={
            "userid": userid_i, 
            "minutes": minutes
        })
        
        if r.status_code == 200:
            stats_data = r.json()
        else:
            print(f"Backend Error: {r.status_code}") # Για debugging
    except Exception as e:
        print(f"Network Error: {e}")

    # 4. Στέλνουμε τα δεδομένα στο stats.html
    return templates.TemplateResponse(
        "stats.html",
        {
            "request": request,
            "active_page": "stats",
            "stats": stats_data,        # Τα δεδομένα από τη βάση
            "current_range": range,     # Για να ξέρει το dropdown τι να δείξει
            "userid": userid_i,          # Για τα JavaScript calls (favorites)
            "is_logged_in": True, 
            "username": username_cookie,
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


@app.get("/register", response_class=HTMLResponse, name="register_page")
async def register_page(request: Request, error: str = None):
    """Registration page"""
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request,
            "error": error
        }
    )

@app.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle registration form submission"""
    try:
        # frontend validation
        if password != confirm_password:
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": "Passwords do not match"
                },
                status_code=400
            )
        
        # Call backend register endpoint
        auth_response = _backend_post(
            "/api/authentication/register",
            json_data={"username": username, "password": password}
        )
        
        backend_status = auth_response.status_code
        
        if backend_status == 200:
            # Registration successful - auto-login user
            user_data = auth_response.json()
            
            # Set cookies and redirect (auto-login)
            response = RedirectResponse(url="/map", status_code=303)
            response.set_cookie("userid", str(user_data["userid"]), httponly=True)
            response.set_cookie("username", user_data["username"], httponly=True)
            return response
            
        else:
            # Registration failed
            try:
                error_data = auth_response.json()
                error_msg = error_data.get("error", "Registration failed")
            except:
                error_msg = "Registration failed"
            
            return templates.TemplateResponse(
                "register.html",
                {
                    "request": request,
                    "error": f"Error {backend_status}: {error_msg}"
                },
                status_code=backend_status
            )
            
    except requests.exceptions.ConnectionError:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Cannot connect to server"
            },
            status_code=500
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