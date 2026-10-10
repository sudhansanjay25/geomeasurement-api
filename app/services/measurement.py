import logging
import shapely
from shapely.geometry.base import BaseGeometry
from app.services.crs import pick_measurement_crs, reproject_geometry

logger = logging.getLogger(__name__)

def ensure_valid(geom: BaseGeometry) -> tuple[BaseGeometry, bool]:
    was_repaired = False
    
    if shapely.has_z(geom):
        geom = shapely.force_2d(geom)
        
    if not geom.is_valid:
        geom = shapely.make_valid(geom)
        was_repaired = True
        
    return geom, was_repaired

def measure_geometry(geom: BaseGeometry, source_crs) -> dict:
    try:
        if geom is None or geom.is_empty:
            return {
                'measurement_type': None, 
                'value': None, 
                'unit': None, 
                'crs_used': None, 
                'note': "empty_geometry"
            }
            
        geom_type = geom.geom_type  # Original type for dispatching
            
        geom, was_repaired = ensure_valid(geom)
        note = "geometry_repaired" if was_repaired else None
        
        if geom_type in ("Point", "MultiPoint"):
            return {
                'measurement_type': None,
                'value': None,
                'unit': None,
                'crs_used': None,
                'note': note or "no_measurement_required"
            }
            
        if geom_type not in ("Polygon", "MultiPolygon", "LineString", "MultiLineString"):
            return {
                'measurement_type': None,
                'value': None,
                'unit': None,
                'crs_used': None,
                'note': "unsupported_geometry"
            }
            
        meas_crs = pick_measurement_crs(geom, source_crs)
        proj_geom = reproject_geometry(geom, source_crs, meas_crs)
        
        if geom_type in ("Polygon", "MultiPolygon"):
            value = abs(float(proj_geom.area))
            unit = "m^2"
            meas_type = "area"
        else: # LineString, MultiLineString
            value = abs(float(proj_geom.length))
            unit = "m"
            meas_type = "length"
            
        epsg = meas_crs.to_epsg()
        crs_str = f"EPSG:{epsg}" if epsg else meas_crs.to_string()
        
        return {
            'measurement_type': meas_type,
            'value': value,
            'unit': unit,
            'crs_used': crs_str,
            'note': note
        }
    except Exception:
        logger.exception("Measurement failed")
        return {
            'measurement_type': None,
            'value': None,
            'unit': None,
            'crs_used': None,
            'note': "measurement_failed"
        }
