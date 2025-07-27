from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import SessionLocal
from datetime import datetime, timedelta
from app.llm_chain import generate
from collections import defaultdict
from dotenv import load_dotenv
import redis
import os

load_dotenv()

router = APIRouter()

REDIS_HOST = os.getenv("REDISHOST")
REDISPASSWORD = os.getenv("REDISPASSWORD")
REDISPORT = os.getenv("REDISPORT")

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDISPORT,
    password=REDISPASSWORD,
    decode_responses=True)

class LLMInput(BaseModel):
    user_input: str
    loggedIn: bool

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
def process_prompt(input: LLMInput, request: Request, db:Session=Depends(get_db)):

    if not input.loggedIn:
        client_ip = request.client.host
        key = f"anon-llm:{client_ip}"
        count = redis_client.get(key)
        if count and int(count) >= 4:
            raise HTTPException(status_code=429, detail="LLM limit reached for guest use. Log in for unlimited LLM usage!")
        else:
            redis_client.incr(key)
            redis_client.expire(key, 86400)

    user_input = input.user_input
    response = generate(user_input)
    query = response.get("sql").replace("%%", "%")
    print("query!", query)
    rows = db.execute(text(query))
    col = rows.keys()
    
    result = [dict(zip(col, row)) for row in rows.fetchall()]
    if not input.loggedIn:
        return {"prompt_results": result, "sql": query, "attempts_left": 4 - int(redis_client.get(key))}
    
    return {"prompt_results": result, "sql": query}
        
@router.get("/grab-initial-events")
def grab_initial_events(db: Session = Depends(get_db)):

    three_weeks_ago = (datetime.utcnow() - timedelta(days=21)).isoformat()
    print(three_weeks_ago)

    query = text(f"""
    SELECT report_id, primary_country, country_lat, country_long, date_report_created, 
    headline_title, headline_summary, source_name, source_homepage, 
    report_url_alias FROM test_reports 
    WHERE date_report_created >= :three_weeks_ago ORDER BY date_report_created DESC;
    """
    )

    rows = db.execute(query, {"three_weeks_ago": three_weeks_ago}).fetchall()

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