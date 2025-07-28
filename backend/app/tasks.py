import requests
from sqlalchemy import create_engine, text
from celery import Celery
from dotenv import load_dotenv
import os
from celery.schedules import crontab
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from app.db_models.worldevent import ReportData
from app.db import engine

load_dotenv()

redis_url =  os.getenv("REDIS_URL") or "redis://localhost:6379/0"

app = Celery("tasks", broker = redis_url, backend = redis_url)
appname = "atlascope"

@app.on_after_configure.connect
def setup_periodic_data_refresh(sender: Celery, **kwargs):
    
    sender.add_periodic_task(
        crontab(minute = 0, hour = '*/3'),
        refresh_db.s()
    )

@app.task
def fetch_reports(start, end, offset = 0, limit = 1000):

    params = {
        "appname": "atlascope",
        "filter[conditions][0][field]": "date.created",
        "filter[conditions][0][value][from]": start.isoformat(),
        "filter[conditions][0][value][to]": end.isoformat(),
        "sort[]": "date.created:desc",
        "fields[include][]": [
            "disaster", 
            "body",
            "id",
            "primary_country", 
            "source", 
            "source.type.name",
            "date", 
            "language", 
            "url_alias"
        ],
        "limit": limit,
        "offset": offset
    }

    base_url = "https://api.reliefweb.int/v1/reports"
    encoded_params = urlencode(params, doseq=True)
    full_url = f"{base_url}?{encoded_params}"

    res = requests.get(full_url)
    data = res.json()
    data = data.get("data")

    results = []
    for report in data:
        report_id = int(report.get("id", None))
        if not report_id:
            continue
        fields = report.get("fields")
        language = fields.get("language", [])[0].get("name", None)
        if language != "English":
            continue
        country_data = fields.get("primary_country", {})
        primary_country = country_data.get("name")
        if primary_country == "World":
            continue
        headline_title = fields.get("title", None)
        if "Location Map" in headline_title or "Monthly Snapshot" in headline_title:
            continue
        country_lat = country_data.get("location", {}).get("lat", None)
        country_long = country_data.get("location", {}).get("lon", None)
        if not country_lat or not country_long:
            continue
        disaster_data = fields.get("disaster", [])
        disaster_status = disaster_data[0].get("status", None) if disaster_data else None
        if disaster_status and disaster_status == "past":
            continue
        disaster_id = disaster_data[0].get("id", None) if disaster_data else None
        disaster_name = disaster_data[0].get("name", None) if disaster_data else None
        disaster_glide = disaster_data[0].get("glide", None) if disaster_data else None
        disaster_type = disaster_data[0].get("type", [])[0].get("name", None) if disaster_data else None
        primary_country_iso3 = country_data.get("iso3")
        primary_country_shortname = country_data.get("shortname", None)
        date = fields.get("date",{}).get("created", None)
        date_report_created = datetime.fromisoformat(date)
        
        headline_summary = fields.get("body", None)
        source_name = fields.get("source", [])[0].get("shortname", None)
        source_homepage = fields.get("source", [])[0].get("homepage", None)
        report_url_alias = fields.get("url_alias", None)
        
        report = ReportData(
            report_id = report_id,
            primary_country = primary_country,
            primary_country_iso3 = primary_country_iso3,
            primary_country_shortname = primary_country_shortname,
            country_lat = country_lat,
            country_long = country_long,
            date_report_created = date_report_created,
            headline_title = headline_title,
            headline_summary = headline_summary,
            language = language,
            source_name = source_name,
            source_homepage = source_homepage,
            report_url_alias = report_url_alias,
            disaster_id = disaster_id,
            disaster_name = disaster_name,
            disaster_glide = disaster_glide,
            disaster_type = disaster_type,
            disaster_status = disaster_status
        )
        results.append(report)
    
    return results

@app.task
def fetch_insert_db(reports):
    initial_query = """
        CREATE TABLE IF NOT EXISTS test_reports (
        report_id INTEGER PRIMARY KEY,
        primary_country TEXT NOT NULL,
        primary_country_iso3 TEXT NOT NULL,
        primary_country_shortname TEXT,
        country_lat REAL NOT NULL,
        country_long REAL NOT NULL,
        geom GEOGRAPHY(Point, 4326),
        date_report_created TIMESTAMP WITH TIME ZONE NOT NULL,
        headline_title TEXT,
        headline_summary TEXT,
        language TEXT,
        source_name TEXT,
        source_homepage TEXT,
        report_url_alias TEXT,
        disaster_id INTEGER,
        disaster_name TEXT,
        disaster_glide TEXT,
        disaster_type TEXT,
        disaster_status TEXT
        );
    """

    insert_query = """
        INSERT INTO test_reports 
        (report_id, primary_country, primary_country_iso3, primary_country_shortname,
        country_lat, country_long, geom, date_report_created, headline_title, headline_summary, 
        language, source_name, source_homepage, report_url_alias, disaster_id, disaster_name, 
        disaster_glide, disaster_type, disaster_status) 
        VALUES (
        :report_id, :primary_country, :primary_country_iso3, 
        :primary_country_shortname,:country_lat, :country_long, 
        ST_SetSRID(ST_MakePoint(:country_long, :country_lat), 4326),
        :date_report_created, :headline_title, :headline_summary, 
        :language, :source_name, :source_homepage, :report_url_alias, 
        :disaster_id, :disaster_name, :disaster_glide, :disaster_type, 
        :disaster_status
        )
        ON CONFLICT (report_id) DO UPDATE SET 
        primary_country = EXCLUDED.primary_country,
        primary_country_iso3 = EXCLUDED.primary_country_iso3,
        primary_country_shortname = EXCLUDED.primary_country_shortname,
        country_lat = EXCLUDED.country_lat,
        country_long = EXCLUDED.country_long,
        date_report_created = EXCLUDED.date_report_created,
        headline_title = EXCLUDED.headline_title,
        headline_summary = EXCLUDED.headline_summary,
        language = EXCLUDED.language,
        source_name = EXCLUDED.source_name,
        source_homepage = EXCLUDED.source_homepage,
        report_url_alias = EXCLUDED.report_url_alias,
        disaster_id = EXCLUDED.disaster_id,
        disaster_name = EXCLUDED.disaster_name,
        disaster_glide = EXCLUDED.disaster_glide,
        disaster_type = EXCLUDED.disaster_type,
        disaster_status = EXCLUDED.disaster_status
    ;
    """

    count = 0
    with engine.connect() as cursor:
        cursor.execute(text(initial_query))
        cursor.commit()
        print("Test Reports table created.")
        for r in reports:
            params = {
                "report_id": r.report_id,
                "primary_country": r.primary_country,
                "primary_country_iso3": r.primary_country_iso3,
                "primary_country_shortname": r.primary_country_shortname,
                "country_lat": r.country_lat,
                "country_long": r.country_long,
                "date_report_created": r.date_report_created,
                "headline_title": r.headline_title,
                "headline_summary": r.headline_summary,
                "language": r.language,
                "source_name": r.source_name,
                "source_homepage": r.source_homepage,
                "report_url_alias": r.report_url_alias,
                "disaster_id": r.disaster_id,
                "disaster_name": r.disaster_name,
                "disaster_glide": r.disaster_glide,
                "disaster_type": r.disaster_type,
                "disaster_status": r.disaster_status
            }
            try:
                cursor.execute(text(insert_query), params)             
                cursor.commit()
                count += 1
            except Exception as e:
                print(e)
                continue
    print(f"Succesfully inserted {count} reports into DB.")

# Refreshes the DB every 3 hours with new reports/events
@app.task
def refresh_db():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now - timedelta(hours=4)
    total_requests = 0
    offset = 0
    limit = 1000
    max_requests = 1000

    while total_requests < max_requests:
        print(f"Fetching offset {offset}")
        reports = fetch_reports(start = start, end = now, offset = offset, limit = limit)
        if not reports:
            break
        fetch_insert_db(reports)
        if len(reports) < limit:
            break
        offset += limit
        total_requests += 1

@app.task
def test_add(name: str):
    query = """
    INSERT INTO test_table (name)
    VALUES (:name)
    """
    with engine.connect() as conn:
        conn.execute(text(query), {"name": name})
        conn.commit()
        print("worked.")

@app.task
def test_table_clear():
    query = """
    DROP TABLE test_reports;
    """
    with engine.connect() as cursor:
        cursor.execute(text(query))
        cursor.commit()
        print("Reset.")

