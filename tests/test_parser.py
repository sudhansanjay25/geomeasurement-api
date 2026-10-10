import pytest
import json
import decimal
import pandas as pd
import numpy as np
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point, LineString
from datetime import datetime, date
from app.services.parser import (
    detect_format,
    read_features,
    make_json_safe,
    gdf_to_feature_records
)
from app.core.errors import FileProcessingError, MissingCRSError, UnsupportedFileTypeError

def test_detect_format():
    assert detect_format(Path("test.shp")) == "shapefile"
    assert detect_format(Path("test.SHP")) == "shapefile"
    assert detect_format(Path("test.kml")) == "kml"
    with pytest.raises(UnsupportedFileTypeError):
        detect_format(Path("test.txt"))

def test_read_features_kml(kml_file):
    gdf = read_features(kml_file, "kml")
    assert len(gdf) == 3
    geom_types = gdf.geometry.type.tolist()
    assert "Polygon" in geom_types
    assert "LineString" in geom_types
    assert "Point" in geom_types
    
    assert gdf.crs is not None
    assert gdf.crs.to_epsg() == 4326

def test_read_features_multi_layer_kml(tmp_path):
    kml = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <Folder>
      <name>Layer1</name>
      <Placemark><Point><coordinates>0,0</coordinates></Point></Placemark>
    </Folder>
    <Folder>
      <name>Layer2</name>
      <Placemark><Point><coordinates>1,1</coordinates></Point></Placemark>
    </Folder>
  </Document>
</kml>
"""
    k_path = tmp_path / "multi.kml"
    k_path.write_text(kml)
    
    gdf = read_features(k_path, "kml")
    assert len(gdf) == 2
    # Ensure they can be converted to records and indexing is 0, 1
    records = gdf_to_feature_records(gdf)
    assert records[0]["feature_index"] == 0
    assert records[1]["feature_index"] == 1

def test_read_features_shapefile(shapefile_zip, tmp_path):
    import zipfile
    dest = tmp_path / "shp_ext"
    with zipfile.ZipFile(shapefile_zip, "r") as zf:
        zf.extractall(dest)
    
    shp_path = dest / "test.shp"
    gdf = read_features(shp_path, "shapefile")
    assert len(gdf) == 2
    assert gdf.crs is not None

def test_read_features_missing_crs(shapefile_zip_no_prj, tmp_path):
    import zipfile
    dest = tmp_path / "shp_noprj_ext"
    with zipfile.ZipFile(shapefile_zip_no_prj, "r") as zf:
        zf.extractall(dest)
        
    shp_path = dest / "test.shp"
    with pytest.raises(MissingCRSError):
        read_features(shp_path, "shapefile")

def test_garbage_kml(tmp_path):
    bad_kml = tmp_path / "bad.kml"
    bad_kml.write_text("not real xml")
    
    with pytest.raises(FileProcessingError):
        read_features(bad_kml, "kml")

def test_make_json_safe():
    assert make_json_safe(float('nan')) is None
    assert make_json_safe(np.nan) is None
    assert make_json_safe(pd.NaT) is None
    assert make_json_safe(float('inf')) is None
    assert make_json_safe(float('-inf')) is None
    
    ts = pd.Timestamp("2020-01-01T12:00:00")
    assert make_json_safe(ts) == "2020-01-01T12:00:00"
    
    dt = date(2021, 1, 1)
    assert make_json_safe(dt) == "2021-01-01"
    
    dec = decimal.Decimal("3.14")
    assert make_json_safe(dec) == 3.14
    
    np_int = np.int64(42)
    assert make_json_safe(np_int) == 42
    assert isinstance(make_json_safe(np_int), int)
    
    assert make_json_safe(b"hello") == "hello"
    
    test_dict = {1: [np.array([1, 2]), pd.NaT], "b": float('inf')}
    res = make_json_safe(test_dict)
    assert res == {"1": [[1, 2], None], "b": None}

def test_json_dumps_end_to_end():
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2020-01-01T12:00:00")],
        "nan_val": [np.nan],
        "np_int": [np.int64(42)],
        "array": [np.array([1, 2, 3])],
        "inf_val": [float('inf')],
        "geometry": [Point(0,0)]
    })
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    
    records = gdf_to_feature_records(gdf)
    assert len(records) == 1
    rec = records[0]
    
    # We drop shapely_geom before json.dumps (which API layer will do)
    del rec["shapely_geom"]
    
    # ensure it doesn't throw a json serialization error, and allow_nan=False catches inf/nan leaks
    json_str = json.dumps(rec, allow_nan=False)
    loaded = json.loads(json_str)
    
    assert loaded["properties"]["timestamp"] == "2020-01-01T12:00:00"
    assert loaded["properties"]["nan_val"] is None
    assert loaded["properties"]["np_int"] == 42
    assert loaded["properties"]["array"] == [1, 2, 3]
    assert loaded["properties"]["inf_val"] is None

def test_gdf_to_feature_records_none_geometry():
    df = pd.DataFrame({
        "name": ["valid", "invalid"],
        "val": [1, 2],
        "geometry": [Point(0,0), None]
    })
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
    
    records = gdf_to_feature_records(gdf)
    assert len(records) == 2
    
    valid_rec = records[0]
    assert valid_rec["geometry_type"] == "Point"
    
    invalid_rec = records[1]
    assert invalid_rec["geometry_type"] == "None"
    assert invalid_rec["geometry"] is None
