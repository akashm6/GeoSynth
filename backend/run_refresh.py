from datetime import datetime, timezone
from app.tasks import refresh_db, backfill_last_5_days

if __name__ == "__main__":
    print(f"[runner] starting at {datetime.now(timezone.utc).isoformat()}")
    backfill_last_5_days.apply()         
    print("[runner] done")
