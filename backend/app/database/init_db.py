from app.database.base import Base
from app.database.connection import SessionLocal, engine
from app.models.role import Role
from app.models.user import User  
from app.models.image import Image  
from app.security.roles import ROLE_NAMES


def init_db():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        for role_id, role_name in ROLE_NAMES.items():
            existing_role = db.query(Role).filter(Role.id == role_id).first()
            if not existing_role:
                db.add(Role(id=role_id, role=role_name))
            else:
                existing_role.role = role_name
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
