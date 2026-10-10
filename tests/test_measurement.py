import pytest
import pyproj
from shapely.geometry import Point, LineString, Polygon, MultiPolygon, GeometryCollection
from app.services.measurement import ensure_valid, measure_geometry

@pytest.mark.parametrize("poly,cx,cy", [
    (Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), 0, 0),
    (Polygon([(45, 45), (46, 45), (46, 46), (45, 46), (45, 45)]), 45.5, 45.5),
    (Polygon([(-70, -33), (-69, -33), (-69, -32), (-70, -32), (-70, -33)]), -69.5, -32.5)
])
def test_polygon_accuracy(poly, cx, cy):
    geod = pyproj.Geod(ellps="WGS84")
    area_geod, _ = geod.geometry_area_perimeter(poly)
    area_geod = abs(area_geod)
    
    meas = measure_geometry(poly, "EPSG:4326")
    area_utm = meas["value"]
    
    diff_pct = abs(area_utm - area_geod) / area_geod
    assert diff_pct < 0.005

def test_line_accuracy():
    line = LineString([(0, 0), (1, 1)])
    geod = pyproj.Geod(ellps="WGS84")
    length_geod = geod.geometry_length(line)
    
    meas = measure_geometry(line, "EPSG:4326")
    length_utm = meas["value"]
    
    diff_pct = abs(length_utm - length_geod) / length_geod
    assert diff_pct < 0.005

def test_axis_order_guard_line():
    # Long E-W line, short N-S, near 60 degrees latitude
    line = LineString([(0, 60), (10, 60.1)])
    geod = pyproj.Geod(ellps="WGS84")
    length_geod = geod.geometry_length(line)
    
    meas = measure_geometry(line, "EPSG:4326")
    length_utm = meas["value"]
    
    diff_pct = abs(length_utm - length_geod) / length_geod
    assert diff_pct < 0.005

def test_geometry_collection_repair():
    # Polygon with a dangling line (spike) will repair to a GeometryCollection (Polygon + LineString)
    poly = Polygon([(0, 0), (2, 0), (2, 2), (0, 2), (0, 0), (3, 0), (0, 0)])
    meas = measure_geometry(poly, "EPSG:4326")
    
    assert meas["note"] == "geometry_repaired"
    assert meas["measurement_type"] == "area"
    # The area should roughly be 4 (2x2 square)
    assert meas["value"] > 3.9

def test_multipolygon_sum():
    p1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    p2 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1), (2, 0)])
    mp = MultiPolygon([p1, p2])
    
    m_p1 = measure_geometry(p1, "EPSG:4326")["value"]
    m_p2 = measure_geometry(p2, "EPSG:4326")["value"]
    m_mp = measure_geometry(mp, "EPSG:4326")["value"]
    
    assert abs(m_mp - (m_p1 + m_p2)) < 0.01

def test_point_and_empty():
    meas = measure_geometry(Point(0,0), "EPSG:4326")
    assert meas["measurement_type"] is None
    assert meas["note"] == "no_measurement_required"
    
    meas_empty = measure_geometry(Polygon(), "EPSG:4326")
    assert meas_empty["note"] == "empty_geometry"
    
    meas_unsupported = measure_geometry(GeometryCollection([Point(0,0)]), "EPSG:4326")
    assert meas_unsupported["note"] == "unsupported_geometry"

def test_bowtie_polygon_repair():
    poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    meas = measure_geometry(poly, "EPSG:4326")
    assert meas["note"] == "geometry_repaired"
    assert meas["measurement_type"] == "area"
    assert meas["value"] > 0

def test_3d_polygon():
    poly2d = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    poly3d = Polygon([(0, 0, 10), (1, 0, 10), (1, 1, 10), (0, 1, 10), (0, 0, 10)])
    
    m2d = measure_geometry(poly2d, "EPSG:4326")
    m3d = measure_geometry(poly3d, "EPSG:4326")
    
    assert abs(m2d["value"] - m3d["value"]) < 0.001

def test_forced_exception(caplog):
    meas = measure_geometry(Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]), "INVALID_CRS")
    assert meas["note"] == "measurement_failed"
    assert "Measurement failed" in caplog.text
