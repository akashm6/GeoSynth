from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import engine, SessionLocal
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
import json

load_dotenv()

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

@router.post("/llm-response/")
def handle_llm_query(prompt: str):
    return

        
@router.get("/ping")
def ping():
    return {"msg": "pong"}