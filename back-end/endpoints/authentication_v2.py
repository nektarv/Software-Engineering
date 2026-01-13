from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import mysql.connector
from utils import DB_CONFIG

router = APIRouter(prefix="/api/authentication", tags=["authentication"])
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT userid, username FROM users WHERE username = %s AND password = %s",
            (credentials.username, credentials.password)
        )
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"}
            )
        
        return user
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

@router.post("/login2", summary="User login with Basic Authentication")
async def login(user: dict = Depends(get_current_user)):
    return {
        "message": "Login successful",
        "userid": user['userid'],
        "username": user['username']
    }

# Optional: Add a logout endpoint if using sessions
@router.post("/logout2", summary="User logout")
async def logout():
    return {"message": "Logout successful"}

# Optional: Check if user is authenticated
@router.get("/me", summary="Get current user info")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "authenticated": True,
        "userid": user['userid'],
        "username": user['username']
    }