from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from dotenv import load_dotenv
from openai import OpenAI
from guidance import models, gen, user, assistant, system, select
import time
import sqlite3
import os
import sqlite3
import requests
from requests.structures import CaseInsensitiveDict
from math import radians, sin, cos, sqrt, atan2
import re
from datetime import datetime

import chromadb
from chromadb.utils import embedding_functions
import json

#When have access to GPU, try this
llm_generated_names = ["Subway Gurney Mall (UTMKL)", "Subway KL East Mall", "Subway One Utama", "Subway Kidzania KL", "Subway Razak City", "Subway C-Mart Changlun", "Subway Aeon Cheras Selatan", "Subway Cahaya Kota Puteri", "Subway Kuala Krai", "Subway IOI Mall Puchong"]
llm_generated = {"Subway Gurney Mall (UTMKL)": {
        "Monday": {"open": "08:00", "close": "21:30"},
        "Tuesday": {"open": "10:00", "close": "21:30"},
        "Wednesday": {"open": "10:00", "close": "21:30"},
        "Thursday": {"open": "10:00", "close": "21:30"},
        "Friday": {"open": "10:00", "close": "21:30"},
        "Saturday": {"open": "10:00", "close": "21:30"},
        "Sunday": {"open": "10:00", "close": "21:30"}
    },
    "Subway KL East Mall": {
        "Monday": {"open": "10:00", "close": "20:00"},
        "Tuesday": {"open": "10:00", "close": "20:00"},
        "Wednesday": {"open": "10:00", "close": "20:00"},
        "Thursday": {"open": "10:00", "close": "20:00"},
        "Friday": {"open": "09:00", "close": "22:00"},
        "Saturday": {"open": "09:00", "close": "22:00"},
        "Sunday": {"open": "10:00", "close": "22:00"}
    },
    "Subway One Utama": {
        "Monday": {"open": "08:00", "close": "22:00"},
        "Tuesday": {"open": "08:00", "close": "22:00"},
        "Wednesday": {"open": "08:00", "close": "22:00"},
        "Thursday": {"open": "08:00", "close": "22:00"},
        "Friday": {"open": "08:00", "close": "22:30"},
        "Saturday": {"open": "08:00", "close": "22:30"},
        "Sunday": {"open": "08:00", "close": "22:00"}
    },
    "Subway Kidzania KL": {
        "Monday": {"open": "10:00", "close": "18:00"},
        "Tuesday": {"open": "10:00", "close": "18:00"},
        "Wednesday": {"open": "10:00", "close": "18:00"},
        "Thursday": {"open": "10:00", "close": "18:00"},
        "Friday": {"open": "10:00", "close": "18:00"},
        "Saturday": {"open": "10:00", "close": "18:00"},
        "Sunday": {"open": "10:00", "close": "18:00"}
    },
    "Subway Razak City": {
        "Monday": {"open": "08:00", "close": "22:00"},
        "Tuesday": {"open": "08:00", "close": "22:00"},
        "Wednesday": {"open": "08:00", "close": "22:00"},
        "Thursday": {"open": "08:00", "close": "22:00"},
        "Friday": {"open": "08:00", "close": "22:00"},
        "Saturday": {"open": "08:00", "close": "22:00"},
        "Sunday": {"open": "08:00", "close": "22:00"}
    },
    "Subway C-Mart Changlun": {
        "Monday": {"open": "10:00", "close": "22:00"},
        "Tuesday": {"open": "10:00", "close": "22:00"},
        "Wednesday": {"open": "10:00", "close": "22:00"},
        "Thursday": {"open": "10:00", "close": "22:00"},
        "Friday": {"open": "10:00", "close": "22:00"},
        "Saturday": {"open": "10:00", "close": "22:00"},
        "Sunday": {"open": "10:00", "close": "22:00"}
    },
    "Subway Aeon Cheras Selatan": {
        "Monday": {"open": "10:00", "close": "22:00"},
        "Tuesday": {"open": "10:00", "close": "22:00"},
        "Wednesday": {"open": "10:00", "close": "22:00"},
        "Thursday": {"open": "10:00", "close": "22:00"},
        "Friday": {"open": "10:00", "close": "22:00"},
        "Saturday": {"open": "10:00", "close": "22:00"},
        "Sunday": {"open": "10:00", "close": "22:00"}
    },
    "Subway Cahaya Kota Puteri": {
        "Monday": {"open": "08:00", "close": "22:00"},
        "Tuesday": {"open": "08:00", "close": "22:00"},
        "Wednesday": {"open": "08:00", "close": "22:00"},
        "Thursday": {"open": "08:00", "close": "22:00"},
        "Friday": {"open": "08:00", "close": "22:00"},
        "Saturday": {"open": "08:00", "close": "22:00"},
        "Sunday": {"open": "08:00", "close": "22:00"}
    },
    "Subway Kuala Krai": {
        "Monday": {"open": "08:00", "close": "22:00"},
        "Tuesday": {"open": "08:00", "close": "22:00"},
        "Wednesday": {"open": "08:00", "close": "22:00"},
        "Thursday": {"open": "08:00", "close": "22:00"},
        "Friday": {"open": "08:00", "close": "22:00"},
        "Saturday": {"open": "08:00", "close": "22:00"},
        "Sunday": {"open": "08:00", "close": "22:00"}
    },
    "Subway IOI Mall Puchong": {
        "Monday": {"open": "10:00", "close": "22:00"},
        "Tuesday": {"open": "10:00", "close": "22:00"},
        "Wednesday": {"open": "10:00", "close": "22:00"},
        "Thursday": {"open": "10:00", "close": "22:00"},
        "Friday": {"open": "10:00", "close": "22:00"},
        "Saturday": {"open": "10:00", "close": "22:00"},
        "Sunday": {"open": "10:00", "close": "22:00"}
    }
}

# Part 0: API Key Configs
load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')

# Part 1: Scraper Configs
def trigger_scraper():
    # Google chrome options for heroku
    from selenium import webdriver
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=chrome_options)

    #Set up sqlite
    connection = sqlite3.connect("scraped_data.db")
    cursor = connection.cursor()
    cursor.execute(""" 
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            address TEXT,
            openingHours TEXT,
            scrapedLat REAL,
            scrapedLong REAL,
            rawExtractionData TEXT,
            UNIQUE(scrapedLat, scrapedLong)
            )
    """)

    try:
        url = "https://www.subway.com.my/find-a-subway"  
        driver.get(url)

        # Step 1: Enter KL into search input
        time.sleep(5) # Have to let it wait to detect my current location or else it will undo the kuala lumpur search
        wait = WebDriverWait(driver, 10)
        search_box = wait.until(EC.presence_of_element_located((By.ID, "fp_searchAddress")))
        search_box.send_keys("kuala lumpur")
        search_box.send_keys(Keys.RETURN)

        # Step 2: Wait a little bit and let the elements regenerate
        time.sleep(3)

        # Step 3: Scrape all the list items
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".fp_listitem")))
        driver.execute_script("""
        let elements = document.querySelectorAll('.fp_listitem');
        elements.forEach(el => el.style.display = 'block');
    """)


        # Step 4: Fill in the data
        wait = WebDriverWait(driver, 10)

        for element in elements:
            text_data = element.text.split("\n") # Observation: the element text always falls under the format (Name \n Address \n Operating hours)
            print(f"Now scanning for {text_data[0]}")
            if len(text_data) <= 2:
                parsed_operating_hours = "Website does not show operating hours"
                continue
            if [item.lower() for item in text_data[2:]] == [item.lower() for item in ["Opening Soon"]]: #Keeping it as lists to make further processing easier
                parsed_operating_hours = "Opening soon"
                continue
            if text_data[0] in llm_generated_names:
                parsed_operating_hours = llm_generated[text_data[0]]
                continue
            if len(text_data) > 2:
                name = text_data[0]
                address = text_data[1]
                try: 
                    operating_hours = text_data[2:]
                    if not isinstance(operating_hours, list):
                        operating_hours = [operating_hours] #Ensure this is always a list to make parse_opening_hours code easier

                    parsed_operating_hours = parse_operating_hours(operating_hours, name)
                    if not parsed_operating_hours or any(parsed_operating_hours.get(day, {}).get(key) is None for day in parsed_operating_hours for key in ['open','close']):
                        parsed_operating_hours = "Error in Parser"                    
                except:
                    parsed_operating_hours = "Error in Parser"
                scraped_lat = element.get_attribute('data-latitude')
                scraped_long = element.get_attribute('data-longitude')
                cursor.execute("""
                    INSERT INTO scraped_data (name, address, openingHours, scrapedLat, scrapedLong, rawExtractionData) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(scrapedLat, scrapedLong) DO NOTHING 
                """, (name, address, json.dumps(parsed_operating_hours), scraped_lat, scraped_long, json.dumps("/n".join(operating_hours))))
                connection.commit() 
            else:
                break
    except Exception as e:
        raise Exception(e)
    finally:
        driver.quit() 
        connection.close()
        return "Scraper Finished Running, check DB"

def save_to_chroma_db():
        # Initialize ChromaDB client
    chroma_client = chromadb.PersistentClient() 
    embeddings = embedding_functions.OpenAIEmbeddingFunction(api_key=openai_api_key)
    collection = chroma_client.get_or_create_collection(name="subway_locations", embedding_function=embeddings)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_data")
    locations = cursor.fetchall()
    for location in locations:
        metadata = {
            "name": location["name"],
            "address": location["address"],
            "opening_hours": location["openingHours"],
            "latitude": f"{location['scrapedLat']}",
            "longitude": f"{location['scrapedLong']}"
        }
        collection.upsert(
            ids=[str(location["id"])],  # Unique ID
            documents=[f"{location['name']} at {location['address']} is open {location['openingHours']}."],
            metadatas=[metadata],
        )


# Part 2: OpenAI Configs
MODEL = "gpt-4o-mini"
model = OpenAI()
default_system_message = "You are a helpful store locator for Subway. Your duty is to assist the user in any of their inquiries about Subway outlets. If the user seems confused, you may suggest to them that you can ask for the nearest outlet or opening hours."

def chat_openai(message, system_message=default_system_message):
    messages = [{"role": "system", "content": system_message}] + [{"role": "user", "content": message}]
    response = model.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content

def intent_classifier(system_prompt, intents, user_input):
    # For now I can use static intents, should be dynamic
    # breakpoint()
    gpt4o = models.OpenAI(MODEL, echo=False)

    with system():
        lm = gpt4o + system_prompt
        
    with user():
        lm += user_input
        lm += "correct intent: "
    
    with assistant():
        # lm += gen(regex="b''", name='intent')
        # lm += gen(regex="(opening closing hours|nearest outlet|not an inquiry or irrelevant inquiry|casual conversation)", name='intent')
        lm += select(intents, name='intent')
        # lm += "correct intent:" + gen(name="intent", stop="'''", temperature=0.2)
   
    print("Intent: ", lm["intent"])
    return lm["intent"]

def get_keyword(user_input):
    llm = models.OpenAI(MODEL)
    with system():
        lm = llm + "You are a helpful store locator for Subway in Malaysia. Your duty is to identify what location the user is referring to in their question. Answer in a single location term. For example: ['Bangsar', 'Shah Alam', 'Kuala Lumpur', 'Penang', 'Mid Valley']"

    with user():
        lm += user_input
        lm += "The user is looking for Subway locations in the area of :"

    with assistant():
        lm += gen(name='answer', max_tokens=100)

    return lm["answer"]

# Functions to call by LLM (Get Distance)
def get_estimated_user_latlong(keyword):
  url = f"https://api.geoapify.com/v1/geocode/search?text={keyword}&bias=countrycode:my&format=json&apiKey=61a4681b133449c7aeffad366860c706"

  headers = CaseInsensitiveDict()
  headers["Accept"] = "application/json"

  resp = requests.get(url, headers=headers)
  lon = resp.json()['results'][0]['lon']
  lat = resp.json()['results'][0]['lat']
  return lon, lat

def get_5_closest_locations(lat, lon):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_data")
    locations = cursor.fetchall()
    conn.close()

    distances = [{
        "name": loc["name"], 
        "address": loc["address"],
        "openingHours": loc["openingHours"],
        "distance": haversine(lat, lon, loc["scrapedLat"], loc["scrapedLong"])
        } for loc in locations]
    
    top_5_sorted_locations = sorted(distances, key=lambda x: x["distance"])[10:]

    #Talk to OpenAI now
    system_message = f"You are a helpful store locator for Subway. Your duty is to assist the user in any of their inquiries about Subway outlets. The user just asked about the nearest subway locations. The locations have been identified to be {top_5_sorted_locations}"
    return system_message

def haversine(lat1, lon1, lat2, lon2):
    r = 6371
    lat1, lon1, lat2,lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return r * c

# Functions to get closing hours
# Map short/long day names
DAYS_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
DAYS_SHORT_MAP = {
    "Sun": "Sunday", "Mon": "Monday", "Tue": "Tuesday", "Wed": "Wednesday", 
    "Thu": "Thursday", "Thur": "Thursday", "Fri": "Friday", "Sat": "Saturday"
}

def clean_day_name(day):
    return re.sub(r"[^a-zA-Z]","",day)

def expand_days(day_text):
    """Expands day ranges and handles '&' cases like 'Saturday, Sunday & Public Holiday'."""
    days = []

    # Split by '&' and ',' to get individual groups (e.g., "Fri, Sat & Sun" → ["Fri", "Sat", "Sun"])
    day_groups = re.split(r"[,&]", day_text)

    for group in day_groups:
        group = group.strip()  # Remove extra spaces

        # Handle "Monday - Friday" format
        if "-" in group:
            start_day, end_day = [clean_day_name(d.strip()) for d in group.split("-")]
            start_day = DAYS_SHORT_MAP.get(start_day, start_day)
            end_day = DAYS_SHORT_MAP.get(end_day, end_day)

            if start_day in DAYS_FULL and end_day in DAYS_FULL:
                start_idx = DAYS_FULL.index(start_day)
                end_idx = DAYS_FULL.index(end_day)

                if start_idx > end_idx:  # Handle wrap-around (e.g., "Fri - Mon")
                    days.extend(DAYS_FULL[start_idx:])  # ["Friday", "Saturday"]
                    days.extend(DAYS_FULL[:end_idx + 1])  # ["Sunday", "Monday"]
                else:
                    days.extend(DAYS_FULL[start_idx:end_idx + 1])
        
        # Single day (e.g., "Saturday", "Sun")
        else:
            clean_day = clean_day_name(group)
            clean_day = DAYS_SHORT_MAP.get(clean_day, clean_day)  # Convert short to full name
            if clean_day in DAYS_FULL:
                days.append(clean_day)

    return days

def convert_time_format(time_str):
    """Converts '0800' or '8:00 PM' into 'HH:MM' 24-hour format."""
    # breakpoint()
    if re.match(r"^\d{4}$", time_str):  # e.g., '0800'
        return f"{time_str[:2]}:{time_str[2:]}"
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        return time_str  # If already correct format

def parse_operating_hours(raw_hours, name):
    """Parses mixed operating hours into structured format."""
    structured_hours = {}

    lines = raw_hours if isinstance(raw_hours, list) else raw_hours.split("\n")
    lines = [re.sub(r"[()\[\]{}]", "", line) for line in lines]
    for line in lines:
        # Handle format: '0800 - 2200 (Sun - Thur)'
        match_short = re.match(r"(\d{4})\s*-\s*(\d{4})\s*\(([\w\s&\-]+)\)", line)
        
        if match_short:
            open_time, close_time, days = match_short.groups()
            for day in expand_days(days):
                structured_hours[day] = {
                    "open": convert_time_format(open_time),
                    "close": convert_time_format(close_time)
                }
            continue

        # Handle format: 'Monday - Sunday, 8:00 AM - 8:00 PM'
        match_long = re.match(
                        r"([\w\s\-,&]+),?\s*"  # Match days (Monday - Friday, Saturday & Sunday, etc.)
                        r"(\d{1,2}:?\d{2}?\s*[APM]*)?\s*"  # Match opening time (optional)
                        r"[-–]\s*"  # Match hyphen or en dash
                        r"(\d{1,2}:?\d{2}?\s*[APM]*)?",  # Match closing time (optional)
                        line
                    )
        
        if match_long:
            days, open_time, close_time = match_long.groups()
            if "Closed" in line:
                open_time, close_time = "Closed", "Closed"

            for day in expand_days(days):
                structured_hours[day] = {
                    "open": convert_time_format(open_time) if open_time else None,
                    "close": convert_time_format(close_time) if close_time else None
                }
    return structured_hours

def get_opening_closing_hours(message):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_data")
    locations = cursor.fetchall()
    conn.close()

    today = datetime.today().strftime("%A")  # Example: "Monday"

    #Another intent classifier portion (TODO: Alternative by using basic similarity search)
    intents = ["earliest opening", "latest opening", "earliest closing", "latest closing"]
    system_prompt = f"""
You are a helpful assistant whose only mission is to identify the correct intents for given user inputs. Your job is to interpret the user's question and decide if the user is asking for the earliest opening hours, latest opening hours, earliest closing hours or latest closing hours.
Please think carefully what the correct intent is based on this few examples. REMEMBER TO ONLY FOLLOW THESE EXAMPLES. DO NOT DEVIATE FROM THIS FORMAT AT ALL.
input: Which are the outlets that closes the latest? [options of intent: {intents}]
correct intent: latest closing
input: Which are the outlets that close the earliest? [options of intent: {intents}]
correct intent: earliest closing
input: Which are the outlets that open the earliest? [options of intent: {intents}]
correct intent: earliest opening
input: Which are the outlets that open the latest? [options of intent: {intents}]
correct intent: latest opening
input: {message} [options of intent: {intents}]

"""
    intent = intent_classifier(system_prompt, intents, message)
    print("subintent identified: ", intent)
    # breakpoint()
    opening_closing_hours = []
    for loc in locations:
        if today in json.loads(loc["openingHours"]).keys():
            opening_closing_hours.append({
                "name": loc["name"],
                "address": loc["address"],
                "opening_hours": json.loads(loc["openingHours"])[today]["open"],
                "closing_hours": json.loads(loc["openingHours"])[today]["close"]
            })
    if intent == "earliest opening":
        earliest_open_time = min(loc["opening_hours"] for loc in opening_closing_hours)
        final_locations = [loc for loc in opening_closing_hours if loc["opening_hours"] == earliest_open_time]
    if intent == "latest opening":
        latest_open_time = min(loc["opening_hours"] for loc in opening_closing_hours)
        final_locations = [loc for loc in opening_closing_hours if loc["opening_hours"] == latest_open_time]
    if intent == "earliest closing":
        earliest_close_time = min(loc["opening_hours"] for loc in opening_closing_hours)
        final_locations = [loc for loc in opening_closing_hours if loc["opening_hours"] == earliest_close_time]
    elif intent == "latest closing":
        latest_close_time = max(loc["closing_hours"] for loc in opening_closing_hours)
        final_locations = [loc for loc in opening_closing_hours if loc["closing_hours"] == latest_close_time]

    system_message = f"You are a helpful assistant that will tell the user which Subway branch has the {intent} hours today. The store(s) with the {intent} time is {final_locations}. Be sure to reply in a humanlike manner"
    return system_message, message

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect("scraped_data.db")
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    return conn

# Part 3: The actual FastAPI

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def test():
    return "FastAPI is running!"

@app.get("/locations")
async def get_locations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scraped_data")
    locations = cursor.fetchall()
    conn.close()

    return [dict(loc) for loc in locations]

@app.on_event("startup")
async def scrape():
    try:
        trigger_scraper()
        print("Scraper finished")
        # save_to_chroma_db()
        # print("Saved to chromaDB")
        return "Scraper finished running, data successfully saved to chromaDB"
    except Exception as e:
        return {"error": e}

@app.get("/chat")
async def chat(message: str):
    try:
        intents = ["opening closing hours", "nearest outlet", "casual conversation"]
        system_prompt = f"""
You are a helpful assistant whose only mission is to identify the correct intents for given user inputs
Please think carefully what the correct intent is based on this few examples. REMEMBER TO ONLY FOLLOW THESE EXAMPLES. DO NOT DEVIATE FROM THIS FORMAT AT ALL.
input: Which are the outlets that closes the latest? [options of intent: {intents}]
correct intent: opening and closing hours
input: Which Subways close the earliest? [options of intent: {intents}]
correct intent: opening and closing hours
input: I crave a Subway. What is the nearest outlet to KLCC?: {intents}]
correct intent: nearest outlet
input: How many outlets are located in Bangsar? [options of intent: {intents}]
correct intent: nearest outlet
input: Hi! How are you? [options of intent: {intents}]
correct intent: casual conversation
input: What's the weather like? [options of intent: {intents}]
correct intent: casual conversation
input: {message} [options of intent: {intents}]

"""
        intent = intent_classifier(system_prompt, intents, message)
        print("Intent identified: ", intent)
        if intent == "nearest outlet":
            keyword = get_keyword(message)
            print("Getting estimated user latlong based on the location: ", keyword)
            lat, long = get_estimated_user_latlong(keyword="Bangsar")
            print(f"Coordinates for {keyword} located. Searching for top 5 locations")
            system_message = get_5_closest_locations(lat, long)
            print("Top 5 locations found, generating response")
            response = chat_openai(system_message=system_message, message=message)
            return response
        elif intent == "opening closing hours":
            print("User is asking for opening or closing hours")
            system_message, message = get_opening_closing_hours(message)
            response = chat_openai(system_message=system_message, message=message)
            return response
        elif intent == "casual conversation":
            print("User is having a casual conversation")
            response = chat_openai(system_message=default_system_message, message=message)
            return response
        else:
            print("Undetected intent")
            response = chat_openai(system_message=default_system_message, message=message)
            return response
    except Exception as e:
        return e


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)