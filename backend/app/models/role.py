from sqlalchemy import Column, Integer, String
from app.database.base import Base

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, unique=True, nullable=False)