# main.py (Updated with Rate Limiting)
import os
import json
import redis
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from sqlalchemy.orm import Session
from database import get_db, URLModel

app = FastAPI(title="Distributed Mini-Link with Rate Limiting")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class URLCreate(BaseModel):
    url: HttpUrl

# --- BASE 62 ENCODER SYSTEM ---
BASE62_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

def encode_base62(num: int) -> str:
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
    global_id = redis_client.incr("global:url:counter")
    offset_id = global_id + 10000000 
    return encode_base62(offset_id)


# --- NEW RATE LIMITER DEPENDENCY ---
def rate_limit_shorten(request: Request):
    """Limits IP addresses to 5 shorten requests per minute."""
    client_ip = request.client.host
    redis_key = f"limit:shorten:{client_ip}"
    
    # Increment the counter for this IP
    current_requests = redis_client.incr(redis_key)
    
    # If it's the first request in this window, set TTL to 60 seconds
    if current_requests == 1:
        redis_client.expire(redis_key, 60)
        
    # If they exceed the limit of 5, reject them
    if current_requests > 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. You can only shorten 5 URLs per minute."
        )


# --- APPLY TO POST ROUTE ---
@app.post("/shorten", dependencies=[Depends(rate_limit_shorten)]) # <-- Add dependency here!
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    long_url_str = str(payload.url)
    
    existing = db.query(URLModel).filter(URLModel.long_url == long_url_str).first()
    if existing:
        redis_client.setex(f"link:{existing.short_code}", 300, existing.long_url)
        return {"short_url": f"http://localhost:8080/{existing.short_code}"}
    
    code = generate_distributed_code()
    
    new_url = URLModel(long_url=long_url_str, short_code=code)
    db.add(new_url)
    db.commit()
    
    redis_client.setex(f"link:{code}", 300, long_url_str)
    
    return {"short_url": f"http://localhost:8080/{code}"}


@app.get("/{short_code}")
def redirect_to_long(short_code: str, request: Request, db: Session = Depends(get_db)):
    cached_url = redis_client.get(f"link:{short_code}")
    
    if cached_url:
        payload = {
            "short_code": short_code,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        redis_client.rpush("queue:analytics", json.dumps(payload))
        return RedirectResponse(url=cached_url, status_code=302)
    
    url_record = db.query(URLModel).filter(URLModel.short_code == short_code).first()
    if not url_record:
        raise HTTPException(status_code=404, detail="Short link not found")
        
    redis_client.setex(f"link:{short_code}", 300, url_record.long_url)
    
    payload = {
        "short_code": short_code,
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    redis_client.rpush("queue:analytics", json.dumps(payload))

    return RedirectResponse(url=url_record.long_url, status_code=302)