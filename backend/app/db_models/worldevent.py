from enum import Enum
from sqlalchemy import create_engine, text
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

connection_string = 'postgresql+psycopg2://postgres:@localhost:5432/globedb_dev'
engine = create_engine(connection_string)

class ReportData(BaseModel):
    report_id: int
    disaster_id: Optional[int]
    primary_country: str
    primary_country_iso3: str
    primary_country_shortname: Optional[str]
    country_lat: float
    country_long: float
    # report-specific
    date_report_created: datetime
    headline_title: Optional[str]
    headline_image_url: Optional[str]
    headline_image_caption: Optional[str]
    headline_summary: Optional[str]
    language: Optional[str]
    source_name: Optional[str]
    source_homepage: Optional[str]
    report_url_alias: Optional[str]
 
# disaster-specific metadata for heatmaps, filters, etc.
class DisasterMetaData(BaseModel):
    disaster_id: int
    date_event: datetime
    disaster_country: Optional[str]
    disaster_country_iso3: Optional[str]
    disaster_lat: float
    disaster_long: float
    disaster_description: Optional[str]
    disaster_name: Optional[str]
    disaster_primary_type: Optional[str]
    disaster_type: Optional[str]
    disaster_status: Optional[str]
    profile_useful_links: list[str]
    disaster_url_alias: Optional[str]
    

class EnrichedEvent(BaseModel):
    report: ReportData
    disaster_metadata: Optional[DisasterMetaData]
           
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
