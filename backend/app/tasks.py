import requests
from sqlalchemy import create_engine, text
from celery import Celery
import json
from datetime import datetime
from db_models.worldevent import ReportData, DisasterMetaData, EnrichedEvent

app = Celery("tasks", broker = "redis://localhost:6379/0", backend="redis://localhost:6379/0")

connection_string = 'postgresql+psycopg2://postgres:@localhost:5432/globedb_dev'
engine = create_engine(connection_string)
appname = "atlascope"

@app.task
def fetch_reports():
    url = ("https://api.reliefweb.int/v1/reports"
           "?appname=atlascope"
           "&filter[field]=headline"
           "&sort[]=date.created:desc&limit=100"
           "&fields[include][]=disaster.id"
           "&fields[include][]=id"
           "&fields[include][]=headline"
           "&fields[include][]=primary_country"
           "&fields[include][]=source"
           "&fields[include][]=date"
           "&fields[include][]=language"
           "&fields[include][]=url_alias"     
    )

    res = requests.get(url)
    data = res.json()
    data = data.get("data")

    results = []
    for report in data:
        fields = report.get("fields")
        #print(fields)
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
    url = ("https://api.reliefweb.int/v1/disasters"
            "?appname=atlascope"
            "&profile=full"
            "&sort[]=date.event:desc&limit=30"
            "&fields[include][]=country"
            "&fields[include][]=date"
            "&fields[include][]=profile.key_content"
            "&fields[include][]=profile.useful_links"
            "&fields[include][]=description"
            "&fields[include][]=name"
            "&fields[include][]=type"
            "&fields[include][]=status"
            "&fields[include][]=url_alias"
    )
    res = requests.get(url)
    data = res.json()
    data = data.get("data")
    results = []
    for report in data:
        print(report)
        fields = report.get("fields")
        disaster_name = fields.get("name", None)
        disaster_description = fields.get("description", None)
        disaster_type = fields.get("type", [])[0].get("name", None)
        date_event = fields.get("date",{}).get("event", None)
        country_data = fields.get("country", [])[0].get("country", {})
        country = country_data.get("name", None)
        country_shortname = country_data.get("shortname", None)
        country_iso3 = country_data.get("iso3", None)
        status = fields.get("status", None)
        profile_data = fields.get


        

        print(report)

    return

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

fetch_reports()
