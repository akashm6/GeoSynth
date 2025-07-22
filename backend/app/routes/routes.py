from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import engine, SessionLocal
from datetime import datetime, timedelta
from app.llm_chain import expand_region_terms, generate
from collections import defaultdict
from dotenv import load_dotenv
from openai import OpenAI
from app.db_models.worldevent import ReportData

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

    readable = last_updated.strftime("%B %d, %Y at %I:%M %p UTC")
    
    return readable

@router.post("/llm-response")
def process_prompt(input: LLMInput, db:Session=Depends(get_db)):
    user_input = input.user_input
    response = generate(user_input)
    query = response.get("sql").replace("%%", "%")
    print("query!", query)
    rows = db.execute(text(query))
    col = rows.keys()
    
    result = [dict(zip(col, row)) for row in rows.fetchall()]

    return {"prompt_results": result, "sql": query}
        
@router.get("/grab-initial-events")
def grab_initial_events(db: Session = Depends(get_db)):

    one_week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    print(one_week_ago)

    query = text(f"""
    SELECT report_id, primary_country, country_lat, country_long, date_report_created, 
    headline_title, headline_summary, source_name, source_homepage, 
    report_url_alias FROM test_reports 
    WHERE date_report_created >= :one_week_ago ORDER BY date_report_created DESC;
    """
    )

    rows = db.execute(query, {"one_week_ago": one_week_ago}).fetchall()

    grouped = defaultdict(list)

    for row in rows:
        report = dict(row._mapping)
        country_lat, country_long = report.get('country_lat'), report.get('country_long')

        key = (country_lat, country_long)
        grouped[key].append(report)

    result = []
    for key, reports in grouped.items():
        result.append({
            "lat": key[0],
            "long": key[1],
            "reports": reports
        })

    return result

@router.get("/ping")
def ping():
    return {"msg": "pong"}