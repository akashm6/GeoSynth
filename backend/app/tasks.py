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
            "disaster.id", 
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
        report_id = int(fields.get("id", None))
        disaster_data = fields.get("disaster", [])
        disaster_id = disaster_data[0].get("id") if disaster_data else None
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
        
        report = ReportData(
            report_id = report_id,
            disaster_id = disaster_id,
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
            report_url_alias = report_url_alias
        )

        results.append(report)

    return results

@app.task
def fetch_disaster_metadata():
    now = datetime.now(timezone.utc).replace(microsecond=0)
    start = now - timedelta(days=150)

    params = {
        "appname": "atlascope",
        "filter[conditions][0][field]": "date.created",
        "filter[conditions][0][value][from]": start.isoformat(),
        "filter[conditions][0][value][to]": now.isoformat(),
        "sort[]": "date.created:desc",
        "fields[include][]": [
            "id", 
            "description", 
            "name",
            "primary_country", 
            "primary_type",
            "date",
            "status",
            "type",
            "profile.useful_links",
            "url_alias"
        ],
        "limit": 100
    }

    base_url = "https://api.reliefweb.int/v1/disasters"
    encoded_params = urlencode(params, doseq=True)
    full_url = f"{base_url}?{encoded_params}"
    res = requests.get(full_url)

    data = res.json()
    data = data.get("data")
    print(data)
    results = []
    for report in data:

        fields = report.get("fields")
        disaster_id = fields.get("id", None)
        date_event = datetime.fromisoformat(fields.get("date", {}).get("changed", None))
        country = fields.get("primary_country", {})
        disaster_country = country.get("shortname", None)
        disaster_country_iso3 = country.get("iso3", None)
        disaster_lat = country.get("location", {}).get("lat")
        disaster_long = country.get("location", {}).get("lon")
        disaster_description = fields.get("description", None)
        disaster_name = fields.get("name", None)
        disaster_type = fields.get("type", [])[0].get("name", None)
        disaster_status = fields.get("status", None)
        profile_data = fields.get("profile", {}).get("active", [])
        profile_useful_links = [link.get("url", None) for link in profile_data.get("useful_links", {}).get("active", [])] if profile_data else None
        disaster_url_alias = fields.get("url_alias", None)
        
        metadata = DisasterMetaData(
            disaster_id = disaster_id,
            date_event = date_event,
            disaster_country = disaster_country,
            disaster_country_iso3 = disaster_country_iso3,
            disaster_lat = disaster_lat,
            disaster_long = disaster_long,
            disaster_description = disaster_description,
            disaster_name = disaster_name,
            disaster_type = disaster_type,
            disaster_status = disaster_status,
            profile_useful_links = profile_useful_links,
            disaster_url_alias = disaster_url_alias
        )

        results.append(metadata)

    return results

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

print(fetch_disaster_metadata())
