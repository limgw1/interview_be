from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

import sqlite3

#Set up Chrome WebDriver
service = Service("chromedriver") 
driver = webdriver.Chrome(service=service)

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