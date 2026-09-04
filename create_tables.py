from backend.app.core.database import Base, engine

# Import all models so SQLAlchemy registers them with Base
from backend.app.models import (
    Role,
    User,
    Product,
    Inspection,
    QualityResult,
)

print("Creating VisionInspect AI database tables...")

Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")