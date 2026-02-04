from sqlalchemy.orm import Session
from src.database import db_engine, SessionLocal
from src.models import Base, User, UserRole
from src.routes.auth.auth_utils import get_password_hash
from src.settings import settings

def create_superadmin(db: Session):
    existing = db.query(User).filter(User.role == UserRole.SUPER_ADMIN).first()
    if existing:
        print(f"Super admin already exists: {existing.email}")
        return
    superadmin = User(
        email=settings.SUPERADMIN_EMAIL,
        hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
        full_name=settings.SUPERADMIN_NAME,
        role=UserRole.SUPER_ADMIN,
        is_active=True
    )
    db.add(superadmin)
    db.commit()
    print(f"Super admin created: {settings.SUPERADMIN_EMAIL}")
    print(f"Password: {settings.SUPERADMIN_PASSWORD}")
    print("Change password after first login!")


ADMIN_EMAIL = "sadit@kusm.edu.np"
ADMIN_PASSWORD = "AdminSecret123!"
ADMIN_NAME = "Administrator"
def create_admin(db: Session):
    existing = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if existing:
        print(f"Admin already exists: {existing.email}")
        return
    admin = User(
        email=ADMIN_EMAIL,
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        full_name=ADMIN_NAME,
        role=UserRole.ADMIN,
        is_active=True
    )
    db.add(admin)
    db.commit()
    print(f"Admin created: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print("Change password after first login!")


def bootstrap_users():
    Base.metadata.create_all(bind=db_engine)
    db: Session = SessionLocal()
    try:
        create_superadmin(db)
        create_admin(db)
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    bootstrap_users()
