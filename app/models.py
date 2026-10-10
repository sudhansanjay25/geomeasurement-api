from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
import uuid
from app.db import Base

class FileStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    stored_path = Column(String, nullable=False)
    crs = Column(String, nullable=True)
    feature_count = Column(Integer, default=0)
    status = Column(Enum(FileStatus), default=FileStatus.PENDING)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    features = relationship("Feature", back_populates="file", cascade="all, delete-orphan")

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String, ForeignKey("uploaded_files.id"), index=True, nullable=False)
    feature_index = Column(Integer, nullable=False)
    geometry_type = Column(String, nullable=False)
    geometry = Column(JSON, nullable=False)
    crs = Column(String, nullable=False)
    properties = Column(JSON, nullable=True)
    
    measurement_type = Column(String, nullable=True) # "area" or "length"
    measurement_value = Column(Float, nullable=True)
    measurement_unit = Column(String, nullable=True)
    measurement_crs = Column(String, nullable=True)
    measurement_note = Column(String, nullable=True)

    file = relationship("UploadedFile", back_populates="features")
