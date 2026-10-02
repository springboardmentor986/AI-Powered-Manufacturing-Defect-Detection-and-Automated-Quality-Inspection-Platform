from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text

from database.connection import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String,
        nullable=False
    )

    stored_filename = Column(
        String,
        nullable=False
    )

    user_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    role = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        nullable=False,
        default="pending"
    )

    result = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )