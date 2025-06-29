from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import engine, SessionLocal
import requests
import json

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/last-updated")
def get_last_updated_time(db: Session = Depends(get_db)):

    query = text("""
    SELECT MAX(date_report_created) FROM test_reports;
    """)
    result = db.execute(query)
    last_updated = result.scalar()
    return {"last_updated": last_updated}
        
@router.get("/ping")
def ping():
    return {"msg": "pong"}