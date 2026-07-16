# worker.py
import os
import time
import json
import redis
from database import SessionLocal, ClickAnalyticsModel

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

print("🚀 Analytics Consumer worker is spinning up... Listening for events...")

while True:
    try:
        # blpop is a blocking operation. It consumes 0% CPU while waiting for an item.
        # It waits for up to 5 seconds. If empty, it returns None and loops back.
        event_data = redis_client.blpop("queue:analytics", timeout=5)
        
        if event_data:
            # event_data format: ('queue:analytics', '{"short_code": "...", "user_agent": "..."}')
            queue_name, raw_json = event_data
            data = json.loads(raw_json)
            
            print(f"📥 [EVENT RECEIVED] Processing click metrics for code: {data['short_code']}")
            
            # Write to PostgreSQL database
            db = SessionLocal()
            analytics_entry = ClickAnalyticsModel(
                short_code=data["short_code"],
                user_agent=data["user_agent"]
            )
            db.add(analytics_entry)
            db.commit()
            db.close()
            
    except Exception as e:
        print(f"⚠️ Worker Error occurred: {e}")
        time.sleep(2) # Prevent rapid fire looping if database drops temporarily