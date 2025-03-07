from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import subprocess

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
        subprocess.run(["python3", "scraper.py"], capture_output=False, text=True)
    except Exception as e:
        return {"error": e.message}
    finally:
        return "Scraping complete"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)