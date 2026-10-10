import math
from functools import lru_cache
import pyproj
import shapely.ops
from shapely.geometry.base import BaseGeometry

def normalize_crs(crs_like) -> pyproj.CRS:
    if isinstance(crs_like, pyproj.CRS):
        return crs_like
    return pyproj.CRS.from_user_input(crs_like)

def is_metric_projected(crs: pyproj.CRS) -> bool:
    if not crs.is_projected:
        return False
    for axis in crs.axis_info:
        if axis.unit_name not in ("metre", "meter"):
            return False
    return True

def utm_epsg_for_lonlat(lon: float, lat: float) -> int:
    if lon >= 180.0:
        zone = 60
    elif lon <= -180.0:
        zone = 1
    else:
        zone = math.floor((lon + 180) / 6) + 1
        
    if lat >= 0:
        return 32600 + zone
    else:
        return 32700 + zone

@lru_cache(maxsize=128)
def get_transformer(src_key: str, dst_key: str):
    return pyproj.Transformer.from_crs(src_key, dst_key, always_xy=True)

def reproject_geometry(geom: BaseGeometry, src, dst) -> BaseGeometry:
    src_crs = normalize_crs(src)
    dst_crs = normalize_crs(dst)
    
    if src_crs == dst_crs:
        return geom
        
    transformer = get_transformer(src_crs.to_string(), dst_crs.to_string())
    return shapely.ops.transform(transformer.transform, geom)

def pick_measurement_crs(geom: BaseGeometry, source_crs) -> pyproj.CRS:
    src = normalize_crs(source_crs)
    if is_metric_projected(src):
        return src
        
    wgs84 = normalize_crs("EPSG:4326")
    
    centroid = geom.centroid
    if src != wgs84:
        centroid = reproject_geometry(centroid, src, wgs84)
        
    lon, lat = centroid.x, centroid.y
    
    if lat > 84.0:
        return pyproj.CRS.from_epsg(3413)
    elif lat < -80.0:
        return pyproj.CRS.from_epsg(3031)
        
    epsg = utm_epsg_for_lonlat(lon, lat)
    return pyproj.CRS.from_epsg(epsg)
