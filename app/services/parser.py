import math
import decimal
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from shapely.geometry import mapping
from pathlib import Path
from datetime import datetime, date
from app.core.errors import FileProcessingError, MissingCRSError, UnsupportedFileTypeError

def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == '.shp':
        return 'shapefile'
    elif ext == '.kml':
        return 'kml'
    raise UnsupportedFileTypeError(f"Unsupported format detected by parser: {ext}")

def read_features(path: Path, fmt: str) -> gpd.GeoDataFrame:
    try:
        if fmt == 'kml':
            try:
                layers = pyogrio.list_layers(path)
            except Exception as e:
                raise FileProcessingError(f"Failed to read KML layers: {e}")
            
            gdfs = []
            if len(layers) > 0:
                for layer_info in layers:
                    layer_name = layer_info[0]
                    gdf = gpd.read_file(path, layer=layer_name, engine="pyogrio")
                    if not gdf.empty:
                        gdfs.append(gdf)
            else:
                gdf = gpd.read_file(path, engine="pyogrio")
                if not gdf.empty:
                    gdfs.append(gdf)
                    
            if gdfs:
                final_gdf = pd.concat(gdfs, ignore_index=True)
            else:
                final_gdf = gpd.GeoDataFrame(geometry=[])
                
            if final_gdf.crs is None:
                final_gdf.set_crs("EPSG:4326", inplace=True)
                
            return final_gdf
        
        else: # shapefile
            try:
                final_gdf = gpd.read_file(path, engine="pyogrio")
            except Exception as e:
                raise FileProcessingError(f"Shapefile decoding error: {e}")
                
            if final_gdf.crs is None:
                raise MissingCRSError("Shapefile is missing CRS information (.prj file might be missing or invalid)")
            return final_gdf
            
    except MissingCRSError:
        raise
    except FileProcessingError:
        raise
    except Exception as e:
        raise FileProcessingError(f"Error reading {fmt} file: {e}")

def make_json_safe(value):
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, np.ndarray):
        return [make_json_safe(v) for v in value.tolist()]
        
    if pd.api.types.is_scalar(value):
        if pd.isna(value):  
            return None
        if isinstance(value, float) and math.isinf(value):
            return None

    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, bytes):
        return value.decode(errors="replace")
        
    return value

def gdf_to_feature_records(gdf: gpd.GeoDataFrame) -> list[dict]:
    records = []
    
    crs_str = None
    if gdf.crs is not None:
        epsg = gdf.crs.to_epsg()
        crs_str = f"EPSG:{epsg}" if epsg else gdf.crs.name
        
    for i, (_, row) in enumerate(gdf.iterrows()):
        geom = row.geometry
        
        if geom is None or (isinstance(geom, float) and pd.isna(geom)) or geom.is_empty:
            geometry_type = "None"
            geometry_mapping = None
            geom = None
        else:
            geometry_type = geom.geom_type
            geometry_mapping = mapping(geom)
            
        properties = {}
        for col in gdf.columns:
            if col != gdf._geometry_column_name:
                properties[col] = make_json_safe(row[col])
                
        records.append({
            "feature_index": i,
            "geometry_type": geometry_type,
            "geometry": geometry_mapping,
            "crs": crs_str,
            "properties": properties,
            "shapely_geom": geom
        })
        
    return records
