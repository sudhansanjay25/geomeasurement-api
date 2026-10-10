from fastapi.testclient import TestClient
from app.main import app
import geopandas as gpd

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_fixtures_exist(kml_file, shapefile_zip, shapefile_zip_no_prj, zip_slip_archive, empty_zip, not_a_zip):
    assert kml_file.exists()
    assert shapefile_zip.exists()
    assert shapefile_zip_no_prj.exists()
    assert zip_slip_archive.exists()
    assert empty_zip.exists()
    assert not_a_zip.exists()

def test_read_kml(kml_file):
    # Geopandas with pyogrio driver for KML
    gdf = gpd.read_file(kml_file, engine="pyogrio")
    assert len(gdf) == 3

def test_read_shapefile(shapefile_zip):
    gdf = gpd.read_file(f"zip://{shapefile_zip}")
    assert len(gdf) == 2
