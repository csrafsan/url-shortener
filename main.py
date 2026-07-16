# main.py
import hashlib
import os
import redis
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import get_db, URLModel

app = FastAPI(title="Mini-Link Monolith with Caching")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connect to Redis using the injected environment variable
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
# decode_responses=True automatically converts Redis bytes to Python strings
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class URLCreate(BaseModel):
    url: HttpUrl

# --- BASE 62 ENCODER SYSTEM ---
BASE62_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode_base62(num: int) -> str:
    """Converts a unique integer counter into a compact short string."""
    if num == 0:
        return BASE62_ALPHABET[0]
    
    arr = []
    base = len(BASE62_ALPHABET)
    while num > 0:
        num, rem = divmod(num, base)
        arr.append(BASE62_ALPHABET[rem])
    arr.reverse()
    return "".join(arr)

def generate_distributed_code() -> str:
    """Uses Redis Atomic Counter to safely issue unique IDs across servers."""
    # redis_client.incr is guaranteed thread-safe across all 5 servers
    global_id = redis_client.incr("global:url:counter")
    
    # Optional offset so your initial short URLs don't look like 'b' or 'c'
    # Starting at 10,000,000 creates a clean 5-character string instantly
    offset_id = global_id + 10000000 
    
    return encode_base62(offset_id)

def generate_short_code(url: str) -> str:
    hash_object = hashlib.md5(url.encode())
    return hash_object.hexdigest()[:6]

@app.post("/shorten")
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    long_url_str = str(payload.url)
    
    # 1. Check if the URL already exists in PostgreSQL to avoid duplicates
    existing = db.query(URLModel).filter(URLModel.long_url == long_url_str).first()
    if existing:
        redis_client.setex(f"link:{existing.short_code}", 300, existing.long_url)
        return {"short_url": f"http://localhost:8080/{existing.short_code}"}
    
    # 2. Safely generate a completely unique, non-colliding short code
    code = generate_distributed_code()
    
    # 3. Commit to database
    new_url = URLModel(long_url=long_url_str, short_code=code)
    db.add(new_url)
    db.commit()
    
    # 4. Save to Redis cache to speed up the immediate next read
    redis_client.setex(f"link:{code}", 300, long_url_str)
    
    return {"short_url": f"http://localhost:8080/{code}"}

# (Keep your @app.get("/{short_code}") endpoint exactly the same as Phase 3)

@app.get("/{short_code}")
def redirect_to_long(short_code: str, db: Session = Depends(get_db)):
    # --- 1. Check Redis Cache First ---
    cached_url = redis_client.get(f"link:{short_code}")
    if cached_url:
        print(f"[CACHE HIT] Serving {short_code} from Redis memory!", flush=True)
        return RedirectResponse(url=cached_url, status_code=302)
    
    # --- 2. Cache Miss: Fallback to SQLite ---
    print(f"[CACHE MISS] Fetching {short_code} from SQLite database...", flush=True)
    url_record = db.query(URLModel).filter(URLModel.short_code == short_code).first()
    
    if not url_record:
        raise HTTPException(status_code=404, detail="Short link not found")
    
    # --- 3. Save to Cache for Next Time ---
    redis_client.setex(f"link:{short_code}", 300, url_record.long_url)
    
    return RedirectResponse(url=url_record.long_url, status_code=302)