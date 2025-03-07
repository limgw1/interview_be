from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

import sqlite3

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
        scrollable_div = driver.find_element(By.ID, "fp_locationlist")
        prev_height = 0

        # while True:
        #     driver.execute_script("arguments[0].scrollTop += 5000;", scrollable_div)
        #     time.sleep(1)  # Wait for new elements to load
            
        #     new_height = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
        #     if new_height == prev_height:  # Stop if no more new elements are loading
        #         break
        #     prev_height = new_height
        # Step 3: Scrape all the list items
        elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".fp_listitem")))
        driver.execute_script("""
        let elements = document.querySelectorAll('.fp_listitem');
        elements.forEach(el => el.style.display = 'block');
    """)


        # Step 4: Fill in the data
        wait = WebDriverWait(driver, 10)
        # Wait until all elements with class 'fp_ll_holder' are present
        # elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".fp_ll_holder")))

        # Loop through each 'fp_ll_holder' element and count its children
        # for index, element in enumerate(elements):
        #     child_elements = element.find_elements(By.XPATH, "./*")  # Select direct children
        #     print(f"Element {index + 1} has {len(child_elements)} children.")
        #     breakpoint()

        for element in elements:
            text_data = element.text.split("\n") # Observation: the element text always falls under the format (Name \n Address \n Operating hours)
            if len(text_data) > 1:
                print(text_data)
                name = text_data[0]
                address = text_data[1]
                try: 
                    operating_hours = '\n'.join(text_data[2:])
                    # breakpoint()
                except:
                    operating_hours = "Not Available"

                scraped_lat = element.get_attribute('data-latitude')
                scraped_long = element.get_attribute('data-longitude')

                cursor.execute("""
                    INSERT INTO scraped_data (name, address, openingHours, scrapedLat, scrapedLong) 
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(scrapedLat, scrapedLong) DO NOTHING 
                """, (name, address, operating_hours, scraped_lat, scraped_long))
                connection.commit() 
            else:
                break
    finally:
        driver.quit() 
        connection.close()
        return "Scraper Finished Running, check DB"

app = FastAPI()

# origins = [
#     "http://localhost",
#     "http://localhost:8080",
#     "http://localhost:8000",
#     "http://localhost:3000",
#     "http://127.0.0.1:5500/*"
#     "http://localhost:5500/*"
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect("scraped_data.db")
    conn.row_factory = sqlite3.Row  # Return results as dictionaries
    return conn

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

@app.get("/trigger_scraper")
async def scrape():
    try:
        output = trigger_scraper()
        return "Scraper finished running"
    except Exception as e:
        return {"error": e.message}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)