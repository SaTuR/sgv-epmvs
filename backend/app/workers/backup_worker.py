import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import SystemSetting
from app.services.backup import run_backup

POLL_SECONDS=30

def should_run(row:SystemSetting):
    if row.backup_run_requested:
        return True
    if not row.backup_enabled:
        return False
    try:
        now=datetime.now(ZoneInfo(row.timezone or settings.tz))
    except Exception:
        now=datetime.now(ZoneInfo(settings.tz))
    if row.backup_time!=now.strftime("%H:%M"):
        return False
    if not row.backup_last_run:
        return True
    last=row.backup_last_run
    if last.tzinfo is None:
        last=last.replace(tzinfo=timezone.utc)
    return last.astimezone(now.tzinfo).date()!=now.date()

def tick():
    db=SessionLocal()
    try:
        row=db.scalar(select(SystemSetting).limit(1))
        if not row or not should_run(row):
            return
        row.backup_run_requested=False
        row.backup_last_status="RUNNING"
        row.backup_last_error=None
        row.backup_last_run=datetime.now(timezone.utc)
        db.commit()
        try:
            filename=run_backup(row.backup_remote_name,row.backup_folder,row.backup_keep_last or 2)
            row.backup_last_status="SUCCESS"
            row.backup_last_filename=filename
            row.backup_last_error=None
        except Exception as exc:
            row.backup_last_status="ERROR"
            row.backup_last_error=str(exc)[:4000]
        db.commit()
    finally:
        db.close()

def main():
    while True:
        try:
            tick()
        except Exception as exc:
            print(f"[backup-worker] {exc}",flush=True)
        time.sleep(POLL_SECONDS)

if __name__=="__main__":
    main()
