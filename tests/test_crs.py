import pytest
import pyproj
from shapely.geometry import Point
from app.services.crs import (
    normalize_crs,
    is_metric_projected,
    utm_epsg_for_lonlat,
    pick_measurement_crs,
    reproject_geometry
)

@pytest.mark.parametrize("lon,lat,expected", [
    (78.7, 10.8, 32644),
    (-70, -33, 32719),
    (0.1, 0, 32631),
    (-0.1, 0, 32630),
    (180, 0, 32660),
    (-180, 0, 32601)
])
def test_utm_epsg_for_lonlat(lon, lat, expected):
    assert utm_epsg_for_lonlat(lon, lat) == expected

def test_pick_measurement_crs():
    geom_4326 = Point(78.7, 10.8)
    crs = pick_measurement_crs(geom_4326, "EPSG:4326")
    assert crs.to_epsg() == 32644
    
    crs_same = pick_measurement_crs(geom_4326, "EPSG:32644")
    assert crs_same.to_epsg() == 32644
    
    geom_feet = Point(980000, 200000)
    crs_from_feet = pick_measurement_crs(geom_feet, "EPSG:2263")
    assert crs_from_feet.to_epsg() == 32618

def test_pick_measurement_crs_polar():
    # Near North Pole (lat 85)
    crs = pick_measurement_crs(Point(0, 85), "EPSG:4326")
    assert crs.to_epsg() == 3413
    # Near South Pole (lat -85)
    crs = pick_measurement_crs(Point(0, -85), "EPSG:4326")
    assert crs.to_epsg() == 3031

def test_axis_order_guard():
    p = Point(10, 20)
    p_proj = reproject_geometry(p, "EPSG:4326", "EPSG:32632")
    assert p_proj.x > 500000
    assert p_proj.y > 2000000
