import sqlite3
import string
import random
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl
from typing import List

# --- Configuration & App Initialization ---
DATA_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
DATABASE = os.path.join(DATA_DIR, 'shortener.db')

app = FastAPI()

# --- Auto-DB Initialization on Startup ---
@app.on_event("startup")
def startup_event():
    if not os.path.exists(DATABASE):
        print("Database not found. Initializing...")
        db = sqlite3.connect(DATABASE)
        schema_path = os.path.join(DATA_DIR, 'schema.sql')
        with open(schema_path, mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
        db.close()
        print("Database initialized successfully.")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class URLItem(BaseModel):
    url: HttpUrl

class URLInfo(BaseModel):
    original_url: HttpUrl
    short_url: str

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_short_code():
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(6))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/shorten", response_model=URLInfo)
async def create_short_url(url_item: URLItem, request: Request):
    original_url = str(url_item.url)
    db = get_db()
    
    existing = db.execute('SELECT short_code FROM urls WHERE original_url = ?', (original_url,)).fetchone()
    if existing:
        short_code = existing['short_code']
    else:
        while True:
            short_code = generate_short_code()
            collision = db.execute('SELECT id FROM urls WHERE short_code = ?', (short_code,)).fetchone()
            if not collision:
                break
        db.execute('INSERT INTO urls (original_url, short_code) VALUES (?, ?)', (original_url, short_code))
        db.commit()
    
    db.close()
    
    base_url = str(request.base_url)
    return {"original_url": original_url, "short_url": f"{base_url}s/{short_code}"}

@app.get("/s/{short_code}")
async def redirect_url(short_code: str):
    db = get_db()
    url_data = db.execute('SELECT original_url FROM urls WHERE short_code = ?', (short_code,)).fetchone()
    db.close()
    
    if url_data:
        return RedirectResponse(url=url_data['original_url'])
    
    raise HTTPException(status_code=404, detail="URL not found")