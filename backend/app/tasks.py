import requests
from sqlalchemy import create_engine, text
from celery import Celery
import json
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from db_models.worldevent import ReportData, DisasterMetaData, EnrichedEvent

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
            "id",
            "headline", 
            "primary_country", 
            "source", 
            "date", 
            "language", 
            "url_alias"
        ],
        "limit": 50
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
        #print(fields)
        report_id = int(fields.get("id", None))
        country_data = fields.get("primary_country", {})
        primary_country = country_data.get("name")
        if primary_country == "World":
            continue
        primary_country_iso3 = country_data.get("iso3")
        primary_country_shortname = country_data.get("shortname", None)
        country_lat = country_data.get("location", {}).get("lat", None)
        country_long = country_data.get("location", {}).get("lon", None)
        date = fields.get("date",{}).get("created", None)
        date_report_created = datetime.fromisoformat(date)
        headline_data = fields.get("headline", {})
        headline_title = headline_data.get("title", None)
        headline_image_url = headline_data.get("image", {}).get("url-large", None)
        headline_image_caption = headline_data.get("image", {}).get("caption", None)
        headline_summary = headline_data.get("summary", None)
        language = fields.get("language", [])[0].get("name", None)
        source_name = fields.get("source", [])[0].get("shortname", None)
        source_homepage = fields.get("source", [])[0].get("homepage", None)
        report_url_alias = fields.get("url_alias", None)
        disaster_data = fields.get("disaster", [])
        disaster_id = disaster_data[0].get("id", None) if disaster_data else None
        disaster_name = disaster_data[0].get("name", None) if disaster_data else None
        disaster_glide = disaster_data[0].get("glide", None) if disaster_data else None
        disaster_type = disaster_data[0].get("type", [])[0].get("name", None) if disaster_data else None
        disaster_status = disaster_data[0].get("status", None) if disaster_data else None
        
        report = ReportData(
            report_id = report_id,
            primary_country = primary_country,
            primary_country_iso3 = primary_country_iso3,
            primary_country_shortname = primary_country_shortname,
            country_lat = country_lat,
            country_long = country_long,
            date_report_created = date_report_created,
            headline_title = headline_title,
            headline_image_url = headline_image_url,
            headline_image_caption = headline_image_caption,
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
    reports = fetch_reports()
    

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

print(fetch_reports())
