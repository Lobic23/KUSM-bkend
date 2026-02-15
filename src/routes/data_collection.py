from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, time, timedelta
from typing import Optional
import asyncio
from sqlalchemy.orm import Session

from src.api import iammeter
from src.routes.auth.auth_utils import require_admin, get_current_user
from src.models import User, DataCollectionScheduleDB
from src.database import get_db

router = APIRouter(prefix="/data-collection", tags=["Data Collection"])


class ScheduleInput(BaseModel):
    start_time: str = Field(..., example="08:00")
    end_time: str = Field(..., example="18:00")
    interval_minutes: int = Field(..., ge=1, le=1440, example=5)

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v):
        try:
            time.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format")

    @field_validator("end_time")
    @classmethod
    def validate_end_after_start(cls, v, info):
        if info.data.get("start_time"):
            start = time.fromisoformat(info.data["start_time"])
            end = time.fromisoformat(v)
            if end <= start:
                raise ValueError("end_time must be after start_time")
        return v


# Global state
class CollectionState:
    def __init__(self):
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.schedule: Optional[ScheduleInput] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

    def is_within_schedule(self) -> bool:
        if not self.schedule:
            return True
        now = datetime.now().time()
        start = time.fromisoformat(self.schedule.start_time)
        end = time.fromisoformat(self.schedule.end_time)
        return start <= now <= end

    def calculate_next_run(self) -> datetime:
        """Calculate when the next collection should run"""
        if not self.schedule:
            # No schedule, just add interval to now
            interval = 5 * 60  # default 5 minutes
            return datetime.now() + timedelta(seconds=interval)

        interval = self.schedule.interval_minutes * 60
        next_time = datetime.now() + timedelta(seconds=interval)

        # If we have a schedule window, check if next run is within it
        now = datetime.now()
        start = time.fromisoformat(self.schedule.start_time)
        end = time.fromisoformat(self.schedule.end_time)

        # Combine today's date with schedule times
        start_datetime = datetime.combine(now.date(), start)
        end_datetime = datetime.combine(now.date(), end)

        # If next run is after end time, schedule for tomorrow's start time
        if next_time.time() > end:
            next_time = datetime.combine(now.date() + timedelta(days=1), start)
        # If we're currently before start time, schedule for today's start time
        elif now.time() < start:
            next_time = start_datetime

        return next_time


state = CollectionState()


async def collection_task():
    """Background task that collects data on schedule"""
    while state.is_running:
        try:
            if state.is_within_schedule():
                print(f"[{datetime.now()}] Collecting data...")
                await asyncio.to_thread(iammeter.store_all_meter_data)
                state.last_run = datetime.now()
                print(f"[{datetime.now()}] Collection complete")
            else:
                print(f"[{datetime.now()}] Outside schedule window, skipping")

        except Exception as e:
            print(f"Collection error: {e}")

        # Calculate next run time
        interval = state.schedule.interval_minutes * 60 if state.schedule else 5 * 60
        state.next_run = datetime.now() + timedelta(seconds=interval)

        # Adjust next_run if outside schedule window
        if state.schedule and not state.is_within_schedule():
            now = datetime.now()
            start = time.fromisoformat(state.schedule.start_time)
            # If outside window, next run is tomorrow's start time
            if now.time() > time.fromisoformat(state.schedule.end_time):
                state.next_run = datetime.combine(now.date() + timedelta(days=1), start)
            else:
                # We're before start time, so next run is today's start time
                state.next_run = datetime.combine(now.date(), start)

        await asyncio.sleep(interval)


@router.get("/status")
async def get_status(current_user: User = Depends(get_current_user)):
    """Get current collection status"""
    return {
        "is_running": state.is_running,
        "schedule": {
            "start_time": state.schedule.start_time,
            "end_time": state.schedule.end_time,
            "interval_minutes": state.schedule.interval_minutes,
        }
        if state.schedule
        else None,
        "last_run": state.last_run.isoformat() if state.last_run else None,
        "next_run": state.next_run.isoformat() if state.next_run else None,
        "is_within_schedule": state.is_within_schedule() if state.is_running else None,
    }


@router.post("/start")
async def start_collection(
    schedule: ScheduleInput,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Start data collection with schedule"""
    if state.is_running:
        raise HTTPException(status_code=400, detail="Already running")

    # Save to database
    db.query(DataCollectionScheduleDB).update({"is_active": False})
    new_schedule = DataCollectionScheduleDB(
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        interval_minutes=schedule.interval_minutes,
        is_active=True,
        created_by=current_user.id,
    )
    db.add(new_schedule)
    db.commit()

    # Start collection
    state.is_running = True
    state.schedule = schedule
    state.next_run = state.calculate_next_run()
    state.task = asyncio.create_task(collection_task())

    return {"message": "Collection started", "is_running": True}


@router.post("/stop")
async def stop_collection(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Stop data collection"""
    if not state.is_running:
        raise HTTPException(status_code=400, detail="Not running")

    state.is_running = False
    if state.task:
        state.task.cancel()
        try:
            await state.task
        except asyncio.CancelledError:
            pass
        state.task = None

    # Mark schedule as inactive in DB
    db.query(DataCollectionScheduleDB).filter(
        DataCollectionScheduleDB.is_active
    ).update({"is_active": False})
    db.commit()

    # Clear next run when stopped
    state.next_run = None

    return {"message": "Collection stopped", "is_running": False}


@router.post("/run-now")
async def run_now(current_user: User = Depends(require_admin)):
    """Manually trigger data collection once"""
    try:
        await asyncio.to_thread(iammeter.store_all_meter_data)
        state.last_run = datetime.now()
        return {
            "message": "Collection executed",
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
