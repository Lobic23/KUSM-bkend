from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Dict
from datetime import datetime
import shutil
from pathlib import Path

from src.ml_model import power_prediction_service

router = APIRouter(
    prefix="/api/prediction",
    tags=["prediction"]
)


# ============================================================================
# Request/Response Models
# ============================================================================
class SinglePredictionRequest(BaseModel):
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    hour: int = Field(..., ge=0, le=23, description="Hour (0-23)")
    minute: int = Field(..., ge=0, le=59, description="Minute (0-59)")


class DayPredictionRequest(BaseModel):
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    interval_minutes: int = Field(5, ge=1, le=60, description="Interval in minutes")


class WeekPredictionRequest(BaseModel):
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    start_day: int = Field(0, ge=0, le=6, description="Starting day (0=Monday)")


class PredictionResponse(BaseModel):
    power_kw: float
    month: int
    day_of_week: int
    hour: int
    minute: int
    timestamp: str


class DayPredictionResponse(BaseModel):
    month: int
    day_of_week: int
    day_name: str
    predictions: List[Dict]
    summary: Dict


class ModelStats(BaseModel):
    mae: float
    rmse: float
    r2: float
    train_samples: int
    test_samples: int
    power_range: Dict
    trained_at: str


# ============================================================================
# Helper Functions
# ============================================================================
def get_day_name(day_of_week: int) -> str:
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    return days[day_of_week]


# ============================================================================
# Routes
# ============================================================================
@router.post("/single", response_model=PredictionResponse)
async def predict_single_point(request: SinglePredictionRequest):
    """
    Predict power consumption for a single time point
    
    Example:
    ```json
    {
        "month": 6,
        "day_of_week": 4,
        "hour": 14,
        "minute": 30
    }
    ```
    """
    try:
        prediction = power_prediction_service.predict_single(
            request.month,
            request.day_of_week,
            request.hour,
            request.minute
        )
        
        return PredictionResponse(
            power_kw=round(prediction, 2),
            month=request.month,
            day_of_week=request.day_of_week,
            hour=request.hour,
            minute=request.minute,
            timestamp=datetime.now().isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/day", response_model=DayPredictionResponse)
async def predict_day(request: DayPredictionRequest):
    """
    Predict power consumption for 24 hours
    
    Example:
    ```json
    {
        "month": 6,
        "day_of_week": 4,
        "interval_minutes": 5
    }
    ```
    """
    try:
        predictions = power_prediction_service.predict_24h(
            request.month,
            request.day_of_week,
            request.interval_minutes
        )
        
        # Calculate summary statistics
        powers = [p['power_kw'] for p in predictions]
        summary = {
            'min_power': round(min(powers), 2),
            'max_power': round(max(powers), 2),
            'avg_power': round(sum(powers) / len(powers), 2),
            'total_energy_kwh': round(sum(powers) * request.interval_minutes / 60, 2),
            'data_points': len(predictions)
        }
        
        return DayPredictionResponse(
            month=request.month,
            day_of_week=request.day_of_week,
            day_name=get_day_name(request.day_of_week),
            predictions=predictions,
            summary=summary
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/week")
async def predict_week(request: WeekPredictionRequest):
    """
    Predict power consumption for a full week
    
    Example:
    ```json
    {
        "month": 6,
        "start_day": 0
    }
    ```
    """
    try:
        week_predictions = power_prediction_service.predict_week(
            request.month,
            request.start_day
        )
        
        # Calculate weekly summary
        all_powers = []
        for day_data in week_predictions.values():
            all_powers.extend([p['power_kw'] for p in day_data])
        
        summary = {
            'min_power': round(min(all_powers), 2),
            'max_power': round(max(all_powers), 2),
            'avg_power': round(sum(all_powers) / len(all_powers), 2),
            'estimated_weekly_energy_kwh': round(sum(all_powers), 2),
        }
        
        return {
            'month': request.month,
            'week_predictions': week_predictions,
            'summary': summary
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/stats", response_model=ModelStats)
async def get_model_stats():
    """Get model performance statistics"""
    try:
        stats = power_prediction_service.get_stats()
        return ModelStats(**stats)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/train")
async def train_new_model(file: UploadFile = File(...)):
    """
    Train a new model from uploaded CSV file
    
    CSV should have columns: Time, Main_Transformer
    """
    try:
        # Save uploaded file temporarily
        temp_path = Path("data/temp_training_data.csv")
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        with temp_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Train model
        stats = power_prediction_service.train_model(str(temp_path))
        
        # Clean up
        temp_path.unlink()
        
        return {
            'message': 'Model trained successfully',
            'stats': stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/load")
async def load_model():
    """Load the saved model from disk"""
    try:
        power_prediction_service.load_model()
        stats = power_prediction_service.get_stats()
        return {
            'message': 'Model loaded successfully',
            'stats': stats
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")


@router.get("/health")
async def health_check():
    """Check if model is loaded and ready"""
    try:
        if power_prediction_service.model is None:
            return {
                'status': 'not_ready',
                'message': 'Model not loaded. Call /api/prediction/load first.'
            }
        
        stats = power_prediction_service.get_stats()
        return {
            'status': 'ready',
            'message': 'Model is loaded and ready',
            'model_info': {
                'r2_score': stats['r2'],
                'trained_at': stats['trained_at']
            }
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }