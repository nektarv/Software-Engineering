from datetime import datetime
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import mysql.connector
from utils import DB_CONFIG, build_error_log


router = APIRouter()


@router.post("/admin/addpoints")
def admin_addpoints():  pass # for now