import pytest
from app.models import UploadedFile, Feature, FileStatus
from app.schemas import FileInfoResponse
from sqlalchemy import inspect
from app.db import Base, create_tables, engine

def test_create_tables(db_session):
    # This just ensures create_tables doesn't throw and actually creates tables
    create_tables()
    inspector = inspect(engine)
    # The engine from app.db is bound to the file database, but db_session creates tables in-memory.
    # To test if the tables exist in the current session's engine:
    session_engine = db_session.get_bind()
    inspector = inspect(session_engine)
    tables = inspector.get_table_names()
    assert "uploaded_files" in tables
    assert "features" in tables

def test_insert_and_query(db_session):
    # Insert UploadedFile
    file_record = UploadedFile(
        filename="test.kml",
        stored_path="uploads/test/test.kml",
        crs="EPSG:4326"
    )
    db_session.add(file_record)
    db_session.commit()
    db_session.refresh(file_record)
    
    assert file_record.id is not None
    assert file_record.status == FileStatus.PENDING
    assert file_record.created_at is not None
    assert file_record.feature_count == 0
    
    # Insert Features
    feature1 = Feature(
        file_id=file_record.id,
        feature_index=0,
        geometry_type="Polygon",
        geometry={"type": "Polygon", "coordinates": [[[0,0], [1,0], [1,1], [0,1], [0,0]]]},
        crs="EPSG:4326",
        properties={"name": "test"}
    )
    feature2 = Feature(
        file_id=file_record.id,
        feature_index=1,
        geometry_type="Point",
        geometry={"type": "Point", "coordinates": [0,0]},
        crs="EPSG:4326",
        properties=None
    )
    db_session.add_all([feature1, feature2])
    db_session.commit()
    
    # Query back
    features = db_session.query(Feature).filter(Feature.file_id == file_record.id).all()
    assert len(features) == 2
    
    # Check JSON round-trip
    poly_feat = next(f for f in features if f.geometry_type == "Polygon")
    assert isinstance(poly_feat.geometry, dict)
    assert poly_feat.geometry["type"] == "Polygon"
    assert poly_feat.properties == {"name": "test"}
    
    pt_feat = next(f for f in features if f.geometry_type == "Point")
    assert pt_feat.properties is None

def test_cascade_delete(db_session):
    file_record = UploadedFile(
        filename="to_delete.kml",
        stored_path="uploads/test/to_delete.kml"
    )
    db_session.add(file_record)
    db_session.commit()
    
    feature = Feature(
        file_id=file_record.id,
        feature_index=0,
        geometry_type="Point",
        geometry={"type": "Point", "coordinates": [0,0]},
        crs="EPSG:4326"
    )
    db_session.add(feature)
    db_session.commit()
    
    # Delete file
    db_session.delete(file_record)
    db_session.commit()
    
    # Feature should be deleted
    features = db_session.query(Feature).all()
    assert len(features) == 0

def test_pydantic_schema_serialization(db_session):
    file_record = UploadedFile(
        filename="schema.kml",
        stored_path="uploads/test/schema.kml"
    )
    db_session.add(file_record)
    db_session.commit()
    db_session.refresh(file_record)
    
    schema = FileInfoResponse.model_validate(file_record)
    assert schema.id == file_record.id
    assert schema.filename == "schema.kml"
    assert schema.status == FileStatus.PENDING
    assert schema.feature_count == 0
    assert schema.created_at == file_record.created_at
