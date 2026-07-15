# main.py
import hashlib
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import get_db, URLModel

app = FastAPI(title="Mini-Link Monolith")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (development only!)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],
)

# Pydantic schema for validating incoming requests
class URLCreate(BaseModel):
    url: HttpUrl

# Crucial Architectural Component: The Short Code Generator
def generate_short_code(url: str) -> str:
    # We take the MD5 hash of the long URL and take the first 6 characters.
    # Note: In a real distributed system, this causes collision issues! 
    # We will fix this scaling problem later in Phase 4.
    hash_object = hashlib.md5(url.encode())
    return hash_object.hexdigest()[:6]

@app.post("/shorten")
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    long_url_str = str(payload.url)
    code = generate_short_code(long_url_str)
    
    # Check if this URL has already been shortened to save space
    existing = db.query(URLModel).filter(URLModel.short_code == code).first()
    if existing:
        return {"short_url": f"http://localhost:8080/{existing.short_code}"}
    
    # Save the new link map to the database
    new_url = URLModel(long_url=long_url_str, short_code=code)
    db.add(new_url)
    db.commit()
    
    return {"short_url": f"http://localhost:8080/{code}"}

@app.get("/{short_code}")
def redirect_to_long(short_code: str, db: Session = Depends(get_db)):
    # Pulling the record out using our indexed short_code
    url_record = db.query(URLModel).filter(URLModel.short_code == short_code).first()
    
    if not url_record:
        raise HTTPException(status_code=404, detail="Short link not found")
        
    # Standard HTTP 302 Temporary Redirect tells the browser to go to the original URL
    return RedirectResponse(url=url_record.long_url, status_code=302)