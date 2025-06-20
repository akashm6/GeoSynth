from enum import Enum
from sqlalchemy import create_engine, text
from pydantic import BaseModel, Optional

connection_string = 'postgresql+psycopg2://postgres:@localhost:5432/globedb_dev'
engine = create_engine(connection_string)

class EventType(str, Enum):
    disaster = "disaster"
    report = "report"

class EventModel(BaseModel):
    event_type: EventType 
    # shared by both
    country: str
    country_iso3: str
    country_shortname: Optional[str]
    status: Optional[str]
    # report-specific
    date_report_created: Optional[str] 
    headline_title: Optional[str]
    headline_image_url: Optional[str]
    headline_summary: Optional[str]
    language: Optional[str]
    source_name: Optional[str]
    source_homepage: Optional[str]
    report_url_alias: Optional[str]
    # disaster-specific
    date_event: Optional[str] 
    disaster_description: Optional[str]
    disaster_name: Optional[str]
    disaster_type: Optional[str]
    profile_key_content: Optional[str] # latest situation reports
    profile_useful_links: Optional[str]
    disaster_url_alias: Optional[str]
           
def test_insert():
    query = """
    INSERT INTO test_table  (name)
    VALUES (:name)
    """
    with engine.connect() as conn:
        try:
            conn.execute(text(query), {"name": "myname"})
            conn.commit()
        except Exception as e:
            print(e)

test_insert()
