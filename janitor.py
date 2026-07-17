# janitor.py
import time
from datetime import datetime
from database import SessionLocal, URLModel

print("🧹 Database Janitor is active... Ready to sweep up dead links!", flush=True)

while True:
    try:
        db = SessionLocal()
        now = datetime.utcnow()
        
        # Find and delete all rows where expires_at is in the past
        expired_links_query = db.query(URLModel).filter(URLModel.expires_at < now)
        expired_count = expired_links_query.count()
        
        if expired_count > 0:
            print(f"🧹 [JANITOR RUN] Found {expired_count} expired links. Purging from database...", flush=True)
            expired_links_query.delete(synchronize_session=False)
            db.commit()
            print("✨ Purge complete. Database optimized.", flush=True)
        else:
            print("💤 [JANITOR RUN] No expired links found. Sleeping...", flush=True)
            
        db.close()
        
    except Exception as e:
        print(f"⚠️ Janitor Error: {e}", flush=True)
        
    # Wait 60 seconds before checking again (use 86400 seconds / 1 day in real production)
    time.sleep(60)