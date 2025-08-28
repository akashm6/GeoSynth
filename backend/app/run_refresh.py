from datetime import datetime, timezone
from app.tasks import refresh_db

if __name__ == "__main__":
    print(f"[runner] starting at {datetime.now(timezone.utc).isoformat()}")
    refresh_db.apply()          
    print("[runner] done")
