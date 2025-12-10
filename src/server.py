from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import meter, oauth, users
from .database import db_engine
from .models import Base
from .api import iammeter
from .init_meter import init_meter
import asyncio
# Create database tables
Base.metadata.create_all(bind=db_engine)
#creating entries in db for existing meters
init_meter()


app = FastAPI(title="KU Smart Meeter", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:5174"], # when in prod use the fend url
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth.router)
app.include_router(users.router)
app.include_router(meter.router)

async def data_collection():
    while True:
        await iammeter.store_all_meter_data();
        await asyncio.sleep(300)

@app.get("/")
async def root():
    asyncio.create_task(data_collection())
    return {"message": "KU Smart Meter API is running", "status": "healthy"}