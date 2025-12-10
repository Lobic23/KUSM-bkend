from sqlalchemy.orm import Session
from .models import MeterDB
from .database import get_db
db: Session = next(get_db())
def init_meter():
    meters = [
        {
            "name": "Physics Department (Block 6)",
            "sn": "CD0FF6AB"
        },
        {
            "name": "Bio-Tech Department (Block 7)",
            "sn": "57DB095D"
        },
        {
            "name": "Block 11 (Department of Civil Engineering)",
            "sn": "DAD94549"
        },
        {
            "name": "Block 10 (Department of Management Information)",
            "sn": "8FA834AC"
        },
        {
            "name": "Block 8 (Department of Electrical and Electronics)",
            "sn": "C249361B"
        },
        {
            "name": "Boys Hostel",
            "sn": "D4C3566B"
        },
        {
            "name": "Main Transformer",
            "sn": "F51C3384"
        },
    ]

    for meter in meters:
        exists = db.query(MeterDB).filter_by(name=meter['name']).first()
        if not exists:
            meter = MeterDB(
                name = meter['name'],
                sn = meter['sn']
            )
            db.add(meter)
            db.commit()
            db.refresh(meter)
