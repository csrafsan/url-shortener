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
from datetime import datetime, timedelta
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="Distributed Mini-Link with Rate Limiting")
# Expose Prometheus metrics at /metrics
Instrumentator().instrument(app).expose(app)
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


def rate_limit_shorten(request: Request):
    """Limit IP addresses to 5 shorten requests per minute."""
    client_ip = request.client.host
    redis_key = f"limit:shorten:{client_ip}"

    current_requests = redis_client.incr(redis_key)
    if current_requests == 1 or redis_client.ttl(redis_key) == -1:
        redis_client.expire(redis_key, 60)

    if current_requests > 5:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. You can only shorten 5 URLs per minute."
        )


@app.post("/shorten", dependencies=[Depends(rate_limit_shorten)])
def shorten_url(payload: URLCreate, db: Session = Depends(get_db)):
    long_url_str = str(payload.url)

    existing = db.query(URLModel).filter(
        URLModel.long_url == long_url_str).first()
    if existing:
        redis_client.setex(
            f"link:{existing.short_code}", 300, existing.long_url)
        return {"short_url": f"http://localhost:9090/{existing.short_code}"}

    code = generate_distributed_code()
    # Calculate expiration date (e.g., 5 minutes from now for testing)
    expiration_time = datetime.utcnow() + timedelta(minutes=5)

    new_url = URLModel(long_url=long_url_str, short_code=code,
                       expires_at=expiration_time)
    db.add(new_url)
    db.commit()

    redis_client.setex(f"link:{code}", 300, long_url_str)

    return {"short_url": f"http://localhost:9090/{code}"}


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

   # Fallback to Database
    url_record = db.query(URLModel).filter(
        URLModel.short_code == short_code).first()

    # --- CHECK IF LINK HAS EXPIRED IN THE DATABASE ---
    if not url_record or url_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=404, detail="This short link has expired or does not exist.")

    # Re-cache if still valid
    remaining_seconds = int(
        (url_record.expires_at - datetime.utcnow()).total_seconds())
    if remaining_seconds > 0:
        redis_client.setex(f"link:{short_code}",
                           remaining_seconds, url_record.long_url)

    payload = {
        "short_code": short_code,
        "user_agent": request.headers.get("user-agent", "unknown")
    }
    redis_client.rpush("queue:analytics", json.dumps(payload))

    return RedirectResponse(url=url_record.long_url, status_code=302)
