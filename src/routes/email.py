import os
from fastapi import HTTPException, APIRouter

from ..api.email_service import send_email

router = APIRouter(prefix="/email", tags=["email"])

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL")

if not ADMIN_EMAIL:
    raise RuntimeError("ADMIN_EMAIL environment variable not set")

@router.post("/send")
async def email_test():
    try:
        await send_email(
            to=ADMIN_EMAIL,
            subject="Smart Meter",
            text="Test Mail"
        )
        return {"success": True, "message": "sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
