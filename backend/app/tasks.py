import requests
from sqlalchemy import create_engine, text
from celery import Celery
import json
from db_models.worldevent import EventModel, EventType

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
           "&fields[include][]=headline"
           "&fields[include][]=country"
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
        country_data = fields.get("country", [{}])[0]
        country = country_data.get("name")
        if country == "World":
            continue
        
        country_iso3 = country_data.get("iso3")
        country_shortname = country_data.get("shortname")
        
        event = EventModel(
            event_type=EventType.report,
            country=country,
            country_iso3=country_iso3,
            country_shortname=country_shortname,
            status=fields.get("status", None),
            date_report_created=fields["date"]["created"],
            headline_title=fields.get("headline", {}).get("title"),
            headline_image_url=fields.get("headline", {}).get("image", {}).get("url"),
            headline_summary=fields.get("headline", {}).get("summary"),
            language=fields.get("language", [])[0].get("name", None),
            source_name=fields.get("source", [])[0].get("name", None),
            source_homepage=fields.get("source", [])[0].get("homepage", None),
            report_url_alias=fields.get("url_alias"),
            date_event = None, 
            disaster_description=None,
            disaster_name=None,
            disaster_type=None,
            profile_key_content=None, # latest situation reports
            profile_useful_links=None,
            disaster_url_alias=None,
        )

        results.append(event)

    return results

@app.task
def fetch_disasters():
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
