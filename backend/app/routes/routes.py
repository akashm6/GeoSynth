from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from db import engine, SessionLocal
from llm_chain import expand_region_terms, generate
from dotenv import load_dotenv
from openai import OpenAI
from db_models.worldevent import ReportData
import requests
import os
import json

load_dotenv()

router = APIRouter()

class LLMInput(BaseModel):
    user_input: str

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

@router.post("/llm-response")
def process_prompt(input: LLMInput, db:Session=Depends(get_db)):
    user_input = input.user_input
    response = generate(user_input)
    sql_query = text(response.get("sql"))
    rows = db.execute(sql_query)
    col = rows.keys()
    
    result = [dict(zip(col, row)) for row in rows.fetchall()]

    return {"prompt_results": result, "sql": sql_query}
        
@router.get("/ping")
def ping():
    return {"msg": "pong"}