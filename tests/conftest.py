import pytest
import zipfile
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point
import os

@pytest.fixture
def kml_file(tmp_path):
    kml_content = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Placemark>
      <name>Test Polygon</name>
      <Polygon>
        <outerBoundaryIs>
          <LinearRing>
            <coordinates>
              78.70,10.80,0 78.71,10.80,0 78.71,10.81,0 78.70,10.81,0 78.70,10.80,0
            </coordinates>
          </LinearRing>
        </outerBoundaryIs>
      </Polygon>
    </Placemark>
    <Placemark>
      <name>Test LineString</name>
      <LineString>
        <coordinates>
          78.70,10.80,0 78.71,10.80,0
        </coordinates>
      </LineString>
    </Placemark>
    <Placemark>
      <name>Test Point</name>
      <Point>
        <coordinates>
          78.705,10.805,0
        </coordinates>
      </Point>
    </Placemark>
  </Document>
</kml>
"""
    file_path = tmp_path / "test.kml"
    file_path.write_text(kml_content)
    return file_path

@pytest.fixture
def shapefile_zip(tmp_path):
    # Create a small geodataframe
    poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    poly2 = Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)])
    gdf = gpd.GeoDataFrame({'geometry': [poly1, poly2], 'name': ['p1', 'p2']}, crs="EPSG:4326")
    
    shp_dir = tmp_path / "shp"
    shp_dir.mkdir()
    shp_path = shp_dir / "test.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile")
    
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file in shp_dir.iterdir():
            zf.write(file, arcname=file.name)
            
    return zip_path

@pytest.fixture
def shapefile_zip_no_prj(tmp_path):
    poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    gdf = gpd.GeoDataFrame({'geometry': [poly1], 'name': ['p1']}, crs="EPSG:4326")
    
    shp_dir = tmp_path / "shp_noprj"
    shp_dir.mkdir()
    shp_path = shp_dir / "test.shp"
    gdf.to_file(shp_path, driver="ESRI Shapefile")
    
    # delete prj file
    prj_file = shp_dir / "test.prj"
    if prj_file.exists():
        prj_file.unlink()
        
    zip_path = tmp_path / "test_noprj.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        for file in shp_dir.iterdir():
            zf.write(file, arcname=file.name)
            
    return zip_path

@pytest.fixture
def zip_slip_archive(tmp_path):
    zip_path = tmp_path / "slip.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        # Note: Some zip tools prevent writing relative paths like this, 
        # but Python's zipfile allows it.
        zf.writestr("../evil.txt", "evil content")
    return zip_path

@pytest.fixture
def empty_zip(tmp_path):
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, 'w') as zf:
        pass
    return zip_path

@pytest.fixture
def not_a_zip(tmp_path):
    file_path = tmp_path / "not_zip.txt"
    file_path.write_text("this is not a zip file")
    return file_path

@pytest.fixture
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.db import Base
    
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
