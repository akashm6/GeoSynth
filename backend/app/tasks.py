import requests
from sqlalchemy import create_engine, text
from celery import Celery
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from db_models.worldevent import ReportData


app = Celery("tasks", broker = "redis://localhost:6379/0", backend="redis://localhost:6379/0")

connection_string = 'postgresql+psycopg2://postgres:@localhost:5432/globedb_dev'
engine = create_engine(connection_string)
appname = "atlascope"

@app.task
def fetch_reports():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now - timedelta(days=1)

    params = {
        "appname": "atlascope",
        "filter[conditions][0][field]": "date.created",
        "filter[conditions][0][value][from]": start.isoformat(),
        "filter[conditions][0][value][to]": now.isoformat(),
        "sort[]": "date.created:desc",
        "fields[include][]": [
            "disaster", 
            "body",
            "id",
            "primary_country", 
            "source", 
            "date", 
            "language", 
            "url_alias"
        ],
        "limit": 100
    }

    base_url = "https://api.reliefweb.int/v1/reports"
    encoded_params = urlencode(params, doseq=True)
    full_url = f"{base_url}?{encoded_params}"

    res = requests.get(full_url)
    data = res.json()
    data = data.get("data")

    results = []
    for report in data:
        fields = report.get("fields")
        language = fields.get("language", [])[0].get("name", None)
        if language != "English":
            continue
        country_data = fields.get("primary_country", {})
        primary_country = country_data.get("name")
        if primary_country == "World":
            continue
        disaster_data = fields.get("disaster", [])
        disaster_status = disaster_data[0].get("status", None) if disaster_data else None
        if disaster_status and disaster_status == "past":
            continue
        disaster_id = disaster_data[0].get("id", None) if disaster_data else None
        disaster_name = disaster_data[0].get("name", None) if disaster_data else None
        disaster_glide = disaster_data[0].get("glide", None) if disaster_data else None
        disaster_type = disaster_data[0].get("type", [])[0].get("name", None) if disaster_data else None
        report_id = int(fields.get("id", None))
        primary_country_iso3 = country_data.get("iso3")
        primary_country_shortname = country_data.get("shortname", None)
        country_lat = country_data.get("location", {}).get("lat", None)
        country_long = country_data.get("location", {}).get("lon", None)
        date = fields.get("date",{}).get("created", None)
        date_report_created = datetime.fromisoformat(date)
        headline_title = fields.get("title", None)
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
def fetch_insert_db():
    test_table_clear()
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
    fetched_reports = fetch_reports()
    with engine.connect() as cursor:
        cursor.execute(text(initial_query))
        cursor.commit()
        print("Test Reports table created.")
        for r in fetched_reports:
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
                print("Insert successful.")
            except Exception as e:
                print(e)
                continue

@app.task
def refresh_data_insert():
    fetch_insert_db()

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

fetch_insert_db()
