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
    "asia": ["India", "China", "Japan", "Indonesia", "Pakistan", "Bangladesh", "Nepal", "Philippines", "Thailand", "Myanmar", "Laos", "Kazakhstan", "Tajikistan", "Turkmenistan", "Russia", "Bhutan", "Sri Lanka", "South Korea", "North Korea", "Vietnam", "Yemen", "Uzbekistan", "Malaysia", "Singapore", 
             "Mongolia", "Bhutan", "Türkiye"],
    "europe": ["Germany", "France", "Italy", "Spain", "United Kingdom", "Sweden", "Norway", "Poland", "Switzerland", "Portugal", "Hungary", "Greece", "Serbia", "Ukraine", "Moldova", "Lithuania", "Finland", "Croatia", "Belarus", "Slovakia", "Austria", "Albania", "Bulgaria", "Latvia", "Russia", "Netherlands", "Ireland", "Moldova", "Bosnia and Herzegovina", 
               "Estonia", "Iceland", "Greenland", "Cyrpus", "Malta"],
    "africa": ["Nigeria", "Ethiopia", "Egypt", "Democratic Republic of the Congo", "Tanzania", "South Africa", "Kenya", "Sudan", "South Sudan", "Uganda", "Algeria", "Angola", "Morocco", "Mozambique", "Ghana", "Madagascar", "Côte d''Ivoire", "Cameroon", "Niger", "Mali", "Burkina Faso", "Malawi", "Zambia", "Chad", "Somalia", "Senegal", "Zimbabwe",
               "Guinea", "Benin", "Rwanda", "Burundi", "Tunisia", "Togo", "Sierra Leone", "Libya", "Congo", "Liberia", "Central African Republic", "Mauritania", "Eritrea", "Namibia", "Gambia", "Gabon", "Botswana", "Lesotho", "Guinea-Bissau", "Equatorial Guinea", "Mauritius", "Eswatini", "Djibouti", "Comoros", "Seychelles"],
    "south america": ["Brazil", "Argentina", "Chile", "Colombia", "Peru", "Bolivia", "Ecuador", "Guyana", "Paraguay", "Suriname", "Uruguay", "Venezuela"],
    "north america": ["United States", "Canada", "Mexico", "Bahamas", "Belize", "Costa Rica", "Cuba", "Dominican Republic", "El Salvador", "Grenada", "Guatemala", "Jamaica", "Haiti", "Honduras", "Nicaragua", "Panama", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Trinidad and Tobago"],
    "middle east": ["Iran", "Iraq", "Syria", "Saudi Arabia", "Jordan", "Israel", "Yemen", "United Arab Emirates", "Lebanon", "Oman", "Qatar", "occupied Palestinian territory", "Kuwait", "Palestine", "Bahrain", "Türkiye"]
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
        "The SQL query should check if a country name matches on either the `primary_country` field or the `primary_country_shortname` field. Ex. (primary_country = 'Mexico' OR primary_country_shortname = 'Mexico')\n"
        "You must always include the `report_id`, `date_report_created`, `headline_title`, `headline_summary`, `source_homepage`, `source_name`, `country_lat`, `country_long`, `primary_country`, `primary_country_shortname`, and `report_url_alias` fields in the SQL query, as it's necessary to parse reports correctly.\n" \
        "If a user's input does not seem to be asking a question, simply return a sql query that returns an empty list.\n"
        "If a user asks about geospatial distances, make sure that your sql query uses ST_DWithin with the `geom` field.\n"
        "If a user asks for \"Turkey\", have the SQL query search for \"Türkiye\" instead for correct results.\n"
        "References to \"Palestine\" should be mapped to \"occupied Palestinian territory\".\n"
        "These are all the possible `disaster_type` fields. If none of these match a user's query, then check for keywords related to the user's query in the `headline_title` or `headline_summary instead.`\n"
        "Mud Slide, Insect Infestation, Tsunami, Cold Wave, Fire, Complex Emergency, Extratropical Cyclone, Drought, Epidemic, Earthquake, Flash Flood, Technological Disaster, Snow Avalanche, Severe Local Storm, Wild Fire, Tropical Cyclone, Flood.\n"
        "There are no other fields that you can use other than the ones below. Do not create new fields.\n"
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



