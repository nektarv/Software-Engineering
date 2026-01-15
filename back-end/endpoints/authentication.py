from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import mysql.connector
from utils import DB_CONFIG, build_error_log

router = APIRouter(prefix="/api/authentication", tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

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