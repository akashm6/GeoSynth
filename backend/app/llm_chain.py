from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers.structured import StructuredOutputParser, ResponseSchema
from dotenv import load_dotenv
import os

load_dotenv()
llm_key = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(model="gpt-4.1-mini", api_key=llm_key)

REGION_MAP = {
    "asia": ["India", "China", "Japan", "Indonesia", "Pakistan", "Bangladesh", "Nepal", "Philippines", "Thailand"],
    "europe": ["Germany", "France", "Italy", "Spain", "United Kingdom", "Sweden", "Norway", "Poland"],
    "africa": ["Nigeria", "South Africa", "Kenya", "Egypt", "Ethiopia", "Ghana", "Morocco"],
    "south america": ["Brazil", "Argentina", "Chile", "Colombia", "Peru"],
    "north america": ["United States", "Canada", "Mexico"],
    "middle east": ["Iran", "Iraq", "Syria", "Saudi Arabia", "Jordan", "Israel", "Yemen", "UAE", "Lebanon"]
}

response_schemas = [
    ResponseSchema(name="sql", description="The SQL query to run"),
    ResponseSchema(name="highlight_condition", description="A condition(s) to highlight"),
]

parser = StructuredOutputParser.from_response_schemas(response_schemas)

def expand_region_terms(user_input: str) -> str:

    prompt = (
        "You are an assistant that turns user questions into SQL queries on a PostgreSQL database of disaster reports.\n"
        "Return a JSON object containing:\n"
        "1. `sql`: A SQL query to fetch relevant data from the `test_reports` table.\n"
        "2. `highlight_condition`: A condition that the frontend can use to highlight specific rows (e.g., \"magnitude > 6\" or \"disaster_status = 'ongoing'\").\n"
        "All entries in the table have only one country as their primary_country.\n"
        "Note: A \"disaster\" should be defined as a report where `disaster_name` OR `disaster_type` is NOT NULL.\n"
        "Do not check for disasters unless the prompt explicitly uses the word \"disaster\".\n"
        "If a user asks for a count of events or disasters, ensure the SQL query always keeps the `country_long` and `country_lat` fields for the country or region the user specifies.\n"
        "The SQL query should check if a country name matches on both the `primary_country` field or the `primary_country_shortname` field.\n"
        "There are no other fields that you can use other than the ones below. Do not create new fields.\n"
        "Also include the `report_url_alias` field in your SQL queries, they are integral.\n"
        "Table: `test_reports`\n"
        "Columns:\n"
        "- report_id: integer\n"
        "- primary_country: text\n"
        "- primary_country_iso3: text\n"
        "- primary_country_shortname: text\n"
        "- country_lat: float\n"
        "- country_long: float\n"
        "- geom: GEOGRAPHY(Point, 4326)\n"
        "- date_report_created: timestamp with timezone\n"
        "- headline_title: text\n"
        "- headline_summary: text\n"
        "- language: text\n"
        "- source_name: text\n"
        "- source_homepage: text\n"
        "- report_url_alias: text\n"
        "- disaster_id: integer\n"
        "- disaster_name: text\n"
        "- disaster_glide: text\n"
        "- disaster_type: text\n"
        "- disaster_status: text\n\n"
        "{format_instructions}\n\n"
        f"User question: {user_input}"
    )

    lowered = prompt.lower()
    for region, countries in REGION_MAP.items():
        if region in lowered:
            country_list = ", ".join(countries)
            prompt += f" (Note: {region.title()} includes {country_list})"

    return PromptTemplate(template=prompt)

def generate(user_input: str):
    full_prompt = expand_region_terms(user_input)    
    chain = full_prompt | llm | parser
    res = chain.invoke(user_input)
    return res



