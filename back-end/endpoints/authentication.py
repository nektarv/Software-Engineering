from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
from utils import DB_CONFIG, build_error_log
import re

router = APIRouter(prefix="/api/authentication", tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str

# authentication endpoint
@router.post("/authentication")
async def login(login_data: LoginRequest, request: Request):
    conn = None
    cursor = None
    
    try:
        # check for empty input
        if not login_data.username or not login_data.password:
            error = build_error_log(
                request, 400, "Bad request",
                "Username and password are required"
            )
            return JSONResponse(status_code=400, content=error)
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # check if a user with that username and password exists
        cursor.execute(
            "SELECT userid, username FROM users WHERE username = %s AND password = %s",
            (login_data.username, login_data.password)
        )
        user = cursor.fetchone()
        
        # covers both "non-existent user" and wrong pw
        if not user:
            error = build_error_log(
                request, 400, "Bad request",
                "Invalid username or password"
            )
            return JSONResponse(status_code=400, content=error)
        
        # print success response
        return {
            "userid": user['userid'],
            "username": user['username']
        }
        
    except mysql.connector.Error as db_error:
        error = build_error_log(
            request, 400, "Bad request",
            f"Database error: {str(db_error)}"
        )
        return JSONResponse(status_code=400, content=error)
        
    except Exception as e:
        error = build_error_log(
            request, 500, "Internal server error",
            str(e)
        )
        return JSONResponse(status_code=500, content=error)
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

# registration endpoint
@router.post("/register")
async def register(register_data: RegisterRequest, request: Request):
    conn = None
    cursor = None
    
    try:
        # empty input
        if not register_data.username or not register_data.password:
            error = build_error_log(
                request, 400, "Bad request",
                "Username and password are required"
            )
            return JSONResponse(status_code=400, content=error)
        
        # username length >= 3
        if len(register_data.username) < 3:
            error = build_error_log(
                request, 400, "Bad request",
                "Username must be at least 3 characters"
            )
            return JSONResponse(status_code=400, content=error)
        
        # username length < 45
        if len(register_data.username) > 45:
            error = build_error_log(
                request, 400, "Bad request", 
                "Username must be less than 45 characters"
            )
            return JSONResponse(status_code=400, content=error)
        
        # correct username format: letters numbers, dots and underscores
        if not re.match(r'^[a-zA-Z0-9._]+$', register_data.username):
            error = build_error_log(
                request, 400, "Bad request",
                "Username can only contain letters, numbers, dots (.), and underscores (_)"
            )
            return JSONResponse(status_code=400, content=error)

        # password length >= 8
        if len(register_data.password) < 8:
            error = build_error_log(
                request, 400, "Bad request",
                "Password must be at least 8 characters"
            )
            return JSONResponse(status_code=400, content=error)
        
        # password length < 45
        if len(register_data.password) > 45:
            error = build_error_log(
                request, 400, "Bad request",
                "Password must be less than 45 characters"
            )
            return JSONResponse(status_code=400, content=error)  
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # check if username already exists
        cursor.execute(
            "SELECT userid FROM users WHERE username = %s",
            (register_data.username,)
        )
        existing_user = cursor.fetchone()
        
        if existing_user:
            error = build_error_log(
                request, 400, "Bad request",
                "This username is taken"
            )
            return JSONResponse(status_code=400, content=error)
        
        # insert new user with password
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (register_data.username, register_data.password)
        )
        conn.commit()
        
        # get new ID
        user_id = cursor.lastrowid
        
        # success response
        return {
            "userid": user_id,
            "username": register_data.username,
            "message": "Registration successful"
        }
        
    except mysql.connector.Error as db_error:
        error = build_error_log(
            request, 400, "Bad request",
            f"Database error: {str(db_error)}"
        )
        return JSONResponse(status_code=400, content=error)
        
    except Exception as e:
        error = build_error_log(
            request, 500, "Internal server error",
            str(e)
        )
        return JSONResponse(status_code=500, content=error)
        
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()