
from src.database import db_engine, get_db
from src.models import Base
from src.init_meter import init_meter


Base.metadata.create_all(bind=db_engine)

db = next(get_db())
try:
    init_meter(db)
finally:
    db.close()