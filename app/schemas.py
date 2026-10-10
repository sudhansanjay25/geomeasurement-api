from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models import FileStatus

class FileInfoResponse(BaseModel):
    id: str
    filename: str
    feature_count: int
    crs: Optional[str]
    status: FileStatus
    error_message: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class MeasurementBlock(BaseModel):
    type: str
    value: float
    unit: str
    crs_used: str

class FeatureMeasurement(BaseModel):
    index: int
    geometry_type: str
    properties: Optional[Dict[str, Any]]
    measurement: Optional[MeasurementBlock]
    note: Optional[str]

class MeasurementSummary(BaseModel):
    feature_count: int
    measured_count: int
    total_area_m2: float
    total_length_m: float
    skipped_count: int

class MeasurementsResponse(BaseModel):
    file_id: str
    summary: MeasurementSummary
    limit: int
    offset: int
    total: int
    features: List[FeatureMeasurement]
