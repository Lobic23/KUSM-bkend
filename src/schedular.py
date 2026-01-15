from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sqlalchemy.orm import Session

from .database import SessionLocal
from .api.billing import calculate_bill

schedular = BackgroundScheduler()

def daily_billing_job():
    db: Session = SessionLocal()
    try:
        now = datetime.now()
        year = now.year
        month = now.month

        calculate_bill(year, month, db)
    finally:
        db.close()



schedular.add_job(
    daily_billing_job,
    trigger="cron",
    hour=0,
    minute=5,   # run at 00:05 every day
)
