from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from .routes import meter, oauth, users, analysis, billing, prediction
from .database import db_engine, get_db
from .models import Base
from .api import iammeter
from .init_meter import init_meter
from .ml_model import power_prediction_service

# Create database tables
Base.metadata.create_all(bind=db_engine)

async def data_collection():
    while True:
        try:
            await asyncio.to_thread(iammeter.store_all_meter_data)
        except Exception as e:
            print(f"Error: {e}")
        await asyncio.sleep(300)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    db = next(get_db())
    try:
        init_meter(db)
    finally:
        db.close()
    
    # Load ML model on startup
    try:
        power_prediction_service.load_model()
        print("✓ ML prediction model loaded successfully")
    except FileNotFoundError:
        print("⚠ ML model not found. Train a model using /api/prediction/train endpoint")
    except Exception as e:
        print(f"⚠ Failed to load ML model: {e}")
    
    # Start data collection task
    task = asyncio.create_task(data_collection())

    try:
        yield
    finally:
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

app = FastAPI(
    title="KU Smart Meeter",
    version="1.0.0",
    lifespan=lifespan,
)

@app.on_event("startup")
def start_scheduler():
    schedular.start()

@app.on_event("shutdown")
def shutdown_scheduler():
    schedular.shutdown()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # when in prod use the fend url
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth.router)
app.include_router(users.router)
app.include_router(meter.router)
app.include_router(analysis.router)
app.include_router(billing.router)
app.include_router(prediction.router)  # NEW: Add prediction router


@app.get("/")
async def root():
    return {"message": "KU Smart Meter API is running", "status": "healthy"}